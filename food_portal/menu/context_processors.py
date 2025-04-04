from .models import MenuItem

def cart_count(request):
    if request.user.is_authenticated:
        cart = request.session.get('cart', {})
        return {'cart_count': sum(cart.values())}
    return {'cart_count': 0}