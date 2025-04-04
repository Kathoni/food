// Toggle cart sidebar
document.addEventListener('DOMContentLoaded', function() {
    const cartLink = document.getElementById('cart-link');
    const cartSidebar = document.getElementById('cart-sidebar');
    
    if (cartLink && cartSidebar) {
        cartLink.addEventListener('click', function(e) {
            e.preventDefault();
            cartSidebar.style.right = cartSidebar.style.right === '0px' ? '-350px' : '0px';
            loadCartItems();
        });
    }
    
    // Close cart when clicking outside
    document.addEventListener('click', function(e) {
        if (cartSidebar && !cartSidebar.contains(e.target)) {
            if (e.target !== cartLink && !cartLink.contains(e.target)) {
                cartSidebar.style.right = '-350px';
            }
        }
    });
    
    // Initialize cart count
    updateCartCount();
});

function updateCartCount() {
    fetch('/get-cart-count/')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.cart_count;
            }
        });
}

function loadCartItems() {
    fetch('/get-cart-items/')
        .then(response => response.json())
        .then(data => {
            const cartItemsContainer = document.getElementById('cart-items');
            const totalAmountElement = document.getElementById('total-amount');
            
            if (data.items && data.items.length > 0) {
                cartItemsContainer.innerHTML = '';
                
                data.items.forEach(item => {
                    const cartItem = document.createElement('div');
                    cartItem.className = 'cart-item';
                    cartItem.innerHTML = `
                        <div class="cart-item-info">
                            <p>${item.name} (${item.quantity})</p>
                            <p>Ksh ${item.price * item.quantity}</p>
                        </div>
                        <div class="cart-item-actions">
                            <button class="decrease-item" data-id="${item.id}">-</button>
                            <button class="increase-item" data-id="${item.id}">+</button>
                            <button class="remove-item" data-id="${item.id}">×</button>
                        </div>
                    `;
                    cartItemsContainer.appendChild(cartItem);
                });
                
                totalAmountElement.textContent = data.total.toFixed(2);
                
                // Add event listeners to cart item buttons
                document.querySelectorAll('.decrease-item').forEach(button => {
                    button.addEventListener('click', function() {
                        updateCartItem(this.dataset.id, -1);
                    });
                });
                
                document.querySelectorAll('.increase-item').forEach(button => {
                    button.addEventListener('click', function() {
                        updateCartItem(this.dataset.id, 1);
                    });
                });
                
                document.querySelectorAll('.remove-item').forEach(button => {
                    button.addEventListener('click', function() {
                        removeCartItem(this.dataset.id);
                    });
                });
                
                // Show checkout button
                document.getElementById('checkout-btn').style.display = 'block';
            } else {
                cartItemsContainer.innerHTML = '<p>Your cart is empty</p>';
                totalAmountElement.textContent = '0.00';
                document.getElementById('checkout-btn').style.display = 'none';
            }
        });
}

function updateCartItem(itemId, change) {
    fetch('/update-cart-item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            item_id: itemId,
            change: change
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadCartItems();
            updateCartCount();
        } else {
            alert(data.message || 'Error updating cart');
        }
    });
}

function removeCartItem(itemId) {
    fetch('/remove-cart-item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            item_id: itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadCartItems();
            updateCartCount();
        } else {
            alert(data.message || 'Error removing item');
        }
    });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}