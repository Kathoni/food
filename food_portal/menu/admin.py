from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MenuItem, Announcement, Order, OrderItem, StockAlert

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available_units', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status',)
    inlines = [OrderItemInline]

admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Announcement)
admin.site.register(Order, OrderAdmin)
admin.site.register(StockAlert)

