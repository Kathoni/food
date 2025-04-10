from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Announcement, Order, OrderItem
import json
from django.contrib import messages
from django.views.decorators.http import require_http_methods

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

@login_required
def checkout(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            cart = request.session.get('cart', {})
            
            if not cart:
                messages.error(request, 'Your cart is empty')
                return redirect('menu_view')
            
            # Create the order
            order = Order.objects.create(
                user=request.user,
                customer_name=name,
                status='pending'
            )
            
            # Create order items
            for item_id, quantity in cart.items():
                try:
                    item = MenuItem.objects.get(id=item_id)
                    OrderItem.objects.create(
                        order=order,
                        menu_item=item,
                        quantity=quantity,
                        price=item.price
                    )
                    # Reduce available units
                    item.available_units -= quantity
                    item.save()
                except MenuItem.DoesNotExist:
                    continue
            
            # Clear the cart
            del request.session['cart']
            request.session.modified = True
            
            messages.success(request, f'Order #{order.id} created successfully!')
            return redirect('order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('menu_view')
    
    return redirect('menu_view')

@login_required
def order_list(request):
    # For workers: show all orders
    if request.user.groups.filter(name='Workers').exists():
        orders = Order.objects.all().order_by('-created_at')
    # For customers: show only their orders
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Ensure the user can only see their own orders unless they're staff
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, "You don't have permission to view this order")
        return redirect('order_list')
    
    order_items = order.orderitem_set.all()
    return render(request, 'orders/detail.html', {
        'order': order,
        'order_items': order_items
    })

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, "You don't have permission to delete this order")
        return redirect('order_list')
    
    if request.method == 'POST':
        order.delete()
        messages.success(request, f'Order #{order_id} has been deleted successfully.')
        return redirect('order_list')
    
    return render(request, 'orders/confirm_delete.html', {'order': order})