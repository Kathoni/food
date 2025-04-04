from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import MenuItem, Announcement, Order, OrderItem, StockAlert
from django.core import serializers
import json
import requests
from django.conf import settings
from django.contrib import messages
import base64
import datetime
from requests.auth import HTTPBasicAuth 
from django.contrib.auth.forms import UserCreationForm
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

@login_required
def admin_menu_view(request):
    if not request.user.is_staff:
        return redirect('menu')
    
    food_items = MenuItem.objects.filter(category='food')
    beverage_items = MenuItem.objects.filter(category='beverage')
    stock_alerts = StockAlert.objects.filter(is_resolved=False)
    
    context = {
        'food_items': food_items,
        'beverage_items': beverage_items,
        'stock_alerts': stock_alerts,
    }
    return render(request, 'admin_menu.html', context)

@login_required
def update_menu_item(request):
    if request.method == 'POST' and request.user.is_staff:
        item_id = request.POST.get('item_id')
        price = request.POST.get('price')
        units = request.POST.get('units')
        
        try:
            item = MenuItem.objects.get(id=item_id)
            item.price = price
            item.available_units = units
            item.save()
            
            # Check if stock is low
            if int(units) == 0:
                alert, created = StockAlert.objects.get_or_create(
                    menu_item=item,
                    is_resolved=False,
                    defaults={'message': f'{item.name} is out of stock!'}
                )
            elif int(units) > 0:
                # Resolve any existing alerts for this item
                StockAlert.objects.filter(menu_item=item, is_resolved=False).update(is_resolved=True)
            
            return JsonResponse({'status': 'success'})
        except (MenuItem.DoesNotExist, ValueError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def create_announcement(request):
    if request.method == 'POST' and request.user.is_staff:
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        if not title or not message:
            return JsonResponse({'status': 'error', 'message': 'Title and message are required'})
        
        Announcement.objects.create(
            title=title,
            message=message,
            created_by=request.user
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def resolve_alert(request, alert_id):
    if request.method == 'POST' and request.user.is_staff:
        try:
            alert = StockAlert.objects.get(id=alert_id)
            alert.is_resolved = True
            alert.save()
            return JsonResponse({'status': 'success'})
        except StockAlert.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alert not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            item = MenuItem.objects.get(id=item_id)
            
            if item.available_units < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Only {item.available_units} units available'
                })
            
            cart = request.session.get('cart', {})
            current_quantity = cart.get(item_id, 0)
            
            # Check if adding this quantity would exceed available units
            if (current_quantity + quantity) > item.available_units:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Cannot add {quantity} more. You already have {current_quantity} in cart.'
                })
            
            cart[item_id] = current_quantity + quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart_count': sum(cart.values()),
                'item_total': cart[item_id]
            })
        except MenuItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid quantity'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
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

@login_required
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