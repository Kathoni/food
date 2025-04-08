document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity controls
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const menuItem = this.closest('.menu-item');
            const itemId = menuItem.dataset.id;
            
            // Show quantity controls
            const quantityControls = menuItem.querySelector('.quantity-controls');
            quantityControls.style.display = 'flex';
            this.style.display = 'none';
            
            // Initialize quantity
            const quantityDisplay = quantityControls.querySelector('.quantity');
            quantityDisplay.textContent = '1';
            
            // Set up confirm button
            const confirmBtn = quantityControls.querySelector('.confirm-add');
            confirmBtn.onclick = function() {
                const quantity = parseInt(quantityDisplay.textContent);
                addToCart(itemId, quantity);
                
                // Reset UI
                quantityControls.style.display = 'none';
                button.style.display = 'block';
            };
        });
    });
    
    // Quantity controls
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('increment')) {
            const quantityDisplay = e.target.parentElement.querySelector('.quantity');
            quantityDisplay.textContent = parseInt(quantityDisplay.textContent) + 1;
        } else if (e.target.classList.contains('decrement')) {
            const quantityDisplay = e.target.parentElement.querySelector('.quantity');
            const current = parseInt(quantityDisplay.textContent);
            if (current > 1) {
                quantityDisplay.textContent = current - 1;
            }
        }
    });
    
    // Cart sidebar toggle
    const cartLink = document.getElementById('cart-link');
    const cartSidebar = document.getElementById('cart-sidebar');
    
    if (cartLink && cartSidebar) {
        cartLink.addEventListener('click', function(e) {
            e.preventDefault();
            cartSidebar.style.right = cartSidebar.style.right === '0px' ? '-350px' : '0px';
            if (cartSidebar.style.right === '0px') {
                loadCartItems();
            }
        });
    }
    
    // Close modal
    document.querySelectorAll('.close').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Checkout form
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const name = document.getElementById('name').value.trim();
            const phone = document.getElementById('phone').value.trim();
            
            if (!name) {
                alert('Please enter your name');
                return;
            }
            
            if (!/^2547\d{8}$/.test(phone)) {
                alert('Please enter a valid M-Pesa phone number (format: 2547XXXXXXXX)');
                return;
            }
            
            fetch('/checkout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    name: name,
                    phone: phone
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = `/order/${data.order_id}/`;
                } else {
                    alert(data.error || 'Error processing your order');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your order');
            });
        });
    }
});

function addToCart(itemId, quantity = 1) {
    fetch('/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showToast('Item added to cart');
        } else {
            alert(data.error || 'Error adding to cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to add item to cart');
    });
}

function loadCartItems() {
    fetch('/get-cart/')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const cartItemsContainer = document.getElementById('cart-items');
            cartItemsContainer.innerHTML = '';
            
            let total = 0;
            
            data.items.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'cart-item';
                itemElement.innerHTML = `
                    <div class="cart-item-info">
                        <h4>${item.name}</h4>
                        <p>${item.quantity} × Ksh ${item.price.toFixed(2)}</p>
                        ${item.available ? '' : '<p class="stock-warning">Out of stock</p>'}
                    </div>
                    <div class="cart-item-total">
                        <p>Ksh ${item.subtotal.toFixed(2)}</p>
                        <button class="remove-item" data-id="${item.id}">×</button>
                    </div>
                `;
                cartItemsContainer.appendChild(itemElement);
                total += item.subtotal;
            });
            
            document.getElementById('total-amount').textContent = total.toFixed(2);
            
            // Add event listeners to remove buttons
            document.querySelectorAll('.remove-item').forEach(button => {
                button.addEventListener('click', function() {
                    removeFromCart(this.dataset.id);
                });
            });
        }
    })
    .catch(error => {
        console.error('Error loading cart:', error);
    });
}

function removeFromCart(itemId) {
    fetch('/remove-from-cart/', {
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
        if (data.success) {
            updateCartCount(data.cart_count);
            loadCartItems();
            showToast('Item removed from cart');
        } else {
            alert(data.error || 'Error removing item');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to remove item');
    });
}

function updateCartCount(count) {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = count;
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

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