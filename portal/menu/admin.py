from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MenuItem, Announcement, Order, StockAlert

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available_units', 'category')
    list_filter = ('category',)
    search_fields = ('name',)



class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'created_at', 'total_amount')

    def total_amount(self, obj):
        # Calculate the total amount for the order by summing up the price of all order items
        return sum(item.item_price * item.quantity for item in obj.items.all())

    total_amount.short_description = 'Total Amount'  # Optional: Set column header
 
class CustomAdminSite(admin.AdminSite):
    class Media:
        css = {
            'all': ('css/custom_admin.css',)
        }

admin.site = CustomAdminSite()
   

admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Announcement)
admin.site.register(Order, OrderAdmin)
admin.site.register(StockAlert)

