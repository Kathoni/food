"""
URL configuration for food_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.menu_view, name='menu'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('get-cart/', views.get_cart, name='get_cart'),
    path('remove-from-cart/', views.remove_from_cart, name= 'remove_from_cart'),
    path('confirm-order/', views.confirm_order, name='confirm_order'),
     path('checkout/', views.checkout_view, name='checkout'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
     path('accounts/logout/', auth_views.LogoutView.as_view(next_page='menu'), name='logout'),
      path('orders/', views.order_list, name='order_list'),
]