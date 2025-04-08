from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import (
    AdminLoginForm, MenuItemForm, 
    AnnouncementForm, OrderStatusForm,
    StockAlertForm, AdminUserCreationForm
)
from .models import MenuItem, Announcement, Order, StockAlert

def admin_check(user):
    return user.is_staff

@login_required
@user_passes_test(admin_check)
def admin_dashboard(request):
    menu_items = MenuItem.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    active_alerts = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'menu_items': menu_items,
        'pending_orders': pending_orders,
        'active_alerts': active_alerts,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(admin_check)
def menu_item_list(request):
    items = MenuItem.objects.all()
    return render(request, 'admin/menu_items/list.html', {'items': items})

@login_required
@user_passes_test(admin_check)
def menu_item_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item created successfully!')
            return redirect('admin_menu_item_list')
    else:
        form = MenuItemForm()
    return render(request, 'admin/menu_items/form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(admin_check)
def menu_item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('admin_menu_item_list')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'admin/menu_items/form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(admin_check)
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('admin_menu_item_list')
    return render(request, 'admin/menu_items/delete.html', {'item': item})

# Similar views for Announcement, Order, and StockAlert would follow the same pattern