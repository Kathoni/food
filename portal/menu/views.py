from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Announcement, Order, OrderItem
import json
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
import base64
import datetime
import requests
from django.conf import settings

def menu_view(request):
    food_items = MenuItem.objects.filter(category='food', available_units__gt=0)
    beverage_items = MenuItem.objects.filter(category='beverage', available_units__gt=0)
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    context = {
        'food_items': food_items,
        'beverage_items': beverage_items,
        'announcements': announcements,
    }
    return render(request, 'menu.html', context)

@require_http_methods(["GET", "POST"])
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            
            try:
                item = MenuItem.objects.get(id=item_id, available_units__gt=0)
                
                if quantity > item.available_units:
                    return JsonResponse({
                        'success': False,
                        'error': f'Only {item.available_units} units available'
                    })
                
                # Initialize cart if it doesn't exist
                if 'cart' not in request.session:
                    request.session['cart'] = {}
                
                # Update cart
                cart = request.session['cart']
                if item_id in cart:
                    if (cart[item_id] + quantity) > item.available_units:
                        return JsonResponse({
                            'success': False,
                            'error': 'Not Available'
                        })
                    cart[item_id] += quantity
                else:
                    cart[item_id] = quantity
                
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'cart_count': sum(cart.values()),
                    'message': 'Item added to cart'
                })
                
            except MenuItem.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Item not available'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

@require_http_methods(["GET"])
def get_cart(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id)
            items.append({
                'id': item.id,
                'name': item.name,
                'price': float(item.price),
                'quantity': quantity,
                'available': item.available_units > 0,
                'subtotal': float(item.price) * quantity
            })
            total += float(item.price) * quantity
        except MenuItem.DoesNotExist:
            continue
    
    return JsonResponse({
        'success': True,
        'items': items,
        'total': total,
        'cart_count': sum(cart.values())
    })

@require_http_methods(["POST"])
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart = request.session.get('cart', {})
        if item_id in cart:
            del cart[item_id]
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'cart_count': sum(cart.values()),
                'message': 'Item removed from cart'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Item not in cart'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
def get_cart_count(request):
    cart = request.session.get('cart', {})
    return JsonResponse({'cart_count': sum(cart.values())})

@csrf_exempt
def get_cart_items(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id)
            items.append({
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'quantity': quantity,
                'subtotal': item.price * quantity,
                'available': item.available_units
            })
            total += item.price * quantity
        except MenuItem.DoesNotExist:
            continue
    
    return JsonResponse({
        'items': items,
        'total': total
    })

# Only logged-in staff/workers can view the list of all orders
@login_required
def order_list(request):
    # Show all orders for staff or workers
    if request.user.is_staff or request.user.groups.filter(name='Workers').exists():
        orders = Order.objects.all().order_by('-created_at')
    else:
        messages.error(request, "You don't have permission to view orders.")
        return redirect('home')  # or a safer page
    return render(request, 'orders/list.html', {'orders': orders})

# View specific order details
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Only allow staff or workers to view any order
    if request.user.is_staff or request.user.groups.filter(name='Workers').exists():
        return render(request, 'orders/detail.html', {'order': order})
    else:
        messages.error(request, "You don't have permission to view this order.")
        return redirect('order_list')

# Delete order (only for staff or workers)
@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.user.is_staff or request.user.groups.filter(name='Workers').exists():
        if request.method == 'POST':
            order.delete()
            return redirect('order_list')
        return render(request, 'orders/confirm_delete.html', {'order': order})
    else:
        messages.error(request, "You don't have permission to delete this order.")
        return redirect('order_list')
def checkout_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for item_id, quantity in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=item_id)
            subtotal = menu_item.price * quantity
            items.append({
                'id': item_id,
                'name': menu_item.name,
                'price': menu_item.price,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except MenuItem.DoesNotExist:
            continue

    context = {
        'items': items,
        'total': total
    }
    return render(request, 'checkout.html', context)
@require_POST
def confirm_order(request):
    customer_name = request.POST.get('name')
    phone = request.POST.get('phone')
    cart = request.session.get('cart', {})

    if not customer_name or not phone or not cart:
        messages.error(request, "All fields are required.")
        return redirect('checkout')

    # Calculate total
    total = 0
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id)
            total += item.price * quantity
        except MenuItem.DoesNotExist:
            continue
    total = int(total) # Convert to integer
    # Call M-Pesa STK push
    payment_response = initiate_mpesa_payment(phone, total)

    if payment_response.get('ResponseCode') == '0':
        # Create the order
        order = Order.objects.create(customer_name=customer_name)
        for item_id, quantity in cart.items():
            try:
                item = MenuItem.objects.get(id=item_id)
                OrderItem.objects.create(
                    order=order,
                    item_name=item.name,
                    item_price=item.price,
                    quantity=quantity
                )

                item.available_units -= quantity
                item.save()

            except MenuItem.DoesNotExist:
                continue

        request.session['cart'] = {}
        messages.success(request, "Order placed! Awaiting payment confirmation on your phone.")
        return redirect('menu')

    else:
        messages.error(request, "Failed to initiate M-Pesa payment. Try again.")
        return redirect('menu')

def initiate_mpesa_payment(phone, amount):
    
    token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(token_url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    access_token = r.json().get('access_token')

    
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        (settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()).decode()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": "174379",
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": "254708374149",
        "PartyB":"174379" ,
        "PhoneNumber": phone,
        "CallBackURL": "https://example.com/api/mpesa/callback",
        "AccountReference": "Order Payment",
        "TransactionDesc": "Food order payment"
    }

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(stk_url, json=payload, headers=headers)
    return response.json()
