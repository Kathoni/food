from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Announcement, Order, OrderItem, StockAlert
import json
import requests
from django.conf import settings
from django.contrib import messages
import base64
import datetime
from requests.auth import HTTPBasicAuth 
from django.contrib import messages


# M-Pesa Utility Functions
def get_mpesa_access_token():
    """Get M-Pesa API access token"""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    try:
        response = requests.get(
            url, 
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting M-Pesa access token: {e}")
        return None

def initiate_stk_push(phone_number, amount, order_id):
    """Initiate STK push to customer's phone"""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'error': 'Failed to get access token'}

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        (settings.MPESA_BUSINESS_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
    ).decode()
    
    payload = {
        "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER{order_id}",
        "TransactionDesc": "Food Order Payment"
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error initiating STK push: {e}")
        return {'error': str(e)}

# View Functions
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


# Add this at the top of views.py
from django.views.decorators.http import require_http_methods

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
                            'error': 'Cannot add more than available stock'
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

@require_http_methods(["POST"])
def checkout(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        phone = data.get('phone')
        
        if not name or not phone:
            return JsonResponse({
                'success': False,
                'error': 'Name and phone number are required'
            })
        
        if not phone.startswith('254') or len(phone) != 12:
            return JsonResponse({
                'success': False,
                'error': 'Invalid phone number format (use 2547XXXXXXXX)'
            })
        
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({
                'success': False,
                'error': 'Your cart is empty'
            })
        
        # Calculate total and verify stock
        total = 0
        order_items = []
        
        for item_id, quantity in cart.items():
            try:
                item = MenuItem.objects.get(id=item_id)
                if item.available_units < quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Not enough stock for {item.name}'
                    })
                
                total += item.price * quantity
                order_items.append({
                    'item': item,
                    'quantity': quantity,
                    'price': item.price
                })
            except MenuItem.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Item {item_id} no longer available'
                })
        
        # Create order (without user if guest)
        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            total_amount=total,
            status='pending'
        )
        
        # Create order items
        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item_data['item'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        # Process M-Pesa payment
        mpesa_response = initiate_stk_push(
            phone_number=phone,
            amount=total,
            order_id=order.id
        )
        
        if 'error' in mpesa_response:
            order.status = 'failed'
            order.save()
            return JsonResponse({
                'success': False,
                'error': mpesa_response['error']
            })
        
        if 'ResponseCode' in mpesa_response and mpesa_response['ResponseCode'] == '0':
            order.mpesa_checkout_id = mpesa_response.get('CheckoutRequestID')
            order.status = 'processing'
            order.save()
            
            # Clear cart only after successful payment initiation
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'message': 'Payment initiated! Please check your phone to complete the payment.'
            })
        else:
            order.status = 'failed'
            order.save()
            return JsonResponse({
                'success': False,
                'error': 'Payment initiation failed'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def update_cart_item(request, item_id):
    if request.method == 'POST':
        action = request.POST.get('action')  # 'increase', 'decrease', or 'remove'
        
        try:
            item = MenuItem.objects.get(id=item_id)
            cart = request.session.get('cart', {})
            
            if item_id not in cart:
                return JsonResponse({'status': 'error', 'message': 'Item not in cart'})
            
            if action == 'increase':
                if item.available_units <= cart[item_id]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Only {item.available_units} units available'
                    })
                cart[item_id] += 1
            elif action == 'decrease':
                if cart[item_id] <= 1:
                    del cart[item_id]
                else:
                    cart[item_id] -= 1
            elif action == 'remove':
                del cart[item_id]
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'})
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart_count': sum(cart.values()),
                'item_quantity': cart.get(item_id, 0)
            })
        except MenuItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def checkout(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.error(request, 'Your cart is empty')
            return redirect('menu')
        
        # Validate phone number
        if not phone_number or not phone_number.startswith('254') or len(phone_number) != 12:
            messages.error(request, 'Please enter a valid M-Pesa phone number (format: 2547XXXXXXXX)')
            return redirect('menu')
        
        # Calculate total
        total = 0
        order_items = []
        
        for item_id, quantity in cart.items():
            try:
                item = MenuItem.objects.get(id=item_id)
                if item.available_units < quantity:
                    messages.error(request, f'Not enough stock for {item.name}')
                    return redirect('menu')
                
                total += item.price * quantity
                order_items.append({
                    'item': item,
                    'quantity': quantity,
                    'price': item.price
                })
            except MenuItem.DoesNotExist:
                messages.error(request, f'Item {item_id} no longer available')
                return redirect('menu')
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            status='pending'
        )
        
        # Create order items and update stock
        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item_data['item'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            
            # Don't update stock yet - wait for payment confirmation
            # item_data['item'].available_units -= item_data['quantity']
            # item_data['item'].save()
        
        # Process M-Pesa payment
        mpesa_response = initiate_stk_push(
            phone_number=phone_number,
            amount=total,
            order_id=order.id
        )
        
        if 'error' in mpesa_response:
            # Handle error case
            order.status = 'failed'
            order.save()
            messages.error(request, f"Payment failed: {mpesa_response['error']}")
            return redirect('menu')
        
        if 'ResponseCode' in mpesa_response and mpesa_response['ResponseCode'] == '0':
            # Payment initiated successfully
            order.mpesa_checkout_id = mpesa_response.get('CheckoutRequestID')
            order.status = 'processing'
            order.save()
            
            # Store order ID in session for callback verification
            request.session['processing_order'] = order.id
            request.session.modified = True
            
            messages.success(request, 'Payment initiated! Please check your phone to complete the payment.')
        else:
            # Payment failed
            order.status = 'failed'
            order.save()
            messages.error(request, 'Payment initiation failed. Please try again.')
        
        # Clear cart only after successful payment initiation
        if order.status == 'processing':
            request.session['cart'] = {}
            request.session.modified = True
        
        return redirect('order_detail', order_id=order.id)
    
    return redirect('menu')

@login_required
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return render(request, 'menu/order_detail.html', {
            'order': order,
            'items': order.orderitem_set.all()
        })
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('menu')

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            callback_data = data.get('Body', {}).get('stkCallback', {})
            result_code = callback_data.get('ResultCode')
            checkout_id = callback_data.get('CheckoutRequestID')
            
            if not checkout_id:
                return JsonResponse({'status': 'error', 'message': 'Missing CheckoutRequestID'}, status=400)
            
            try:
                order = Order.objects.get(mpesa_checkout_id=checkout_id)
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
            
            if result_code == '0':
                # Successful payment
                metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = next(
                    (item.get('Value') for item in metadata if item.get('Name') == 'MpesaReceiptNumber'),
                    None
                )
                
                order.status = 'completed'
                order.mpesa_receipt = receipt_number
                order.save()
                
                # Now update stock levels
                for item in order.orderitem_set.all():
                    menu_item = item.menu_item
                    menu_item.available_units -= item.quantity
                    menu_item.save()
                
                # Send confirmation email could go here
                
                return JsonResponse({'status': 'success'})
            else:
                # Failed payment
                order.status = 'failed'
                order.save()
                return JsonResponse({'status': 'error', 'message': 'Payment failed'}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def get_cart_count(request):
    cart = request.session.get('cart', {})
    return JsonResponse({'cart_count': sum(cart.values())})

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