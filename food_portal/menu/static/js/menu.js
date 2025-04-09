document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initCartFunctionality();
    initMenuItems();
    initCheckoutForm();
});

/* ======================
   CART FUNCTIONALITY
   ====================== */
function initCartFunctionality() {
    // Cart elements
    const cartLink = document.getElementById('cart-link');
    const cartSidebar = document.getElementById('cart-sidebar');
    
    if (cartLink && cartSidebar) {
        // Toggle cart sidebar
        cartLink.addEventListener('click', function(e) {
            e.preventDefault();
            cartSidebar.style.right = cartSidebar.style.right === '0px' ? '-350px' : '0px';
            if (cartSidebar.style.right === '0px') {
                loadCartItems();
            }
        });
        
        // Close cart when clicking outside
        document.addEventListener('click', function(e) {
            if (!cartSidebar.contains(e.target) && e.target !== cartLink && !cartLink.contains(e.target)) {
                cartSidebar.style.right = '-350px';
            }
        });
    }
    
    // Initialize cart count
    updateCartCount();
}

/* ======================
   MENU ITEMS FUNCTIONALITY
   ====================== */
function initMenuItems() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const menuItem = this.closest('.menu-item');
            if (!menuItem) return;
            
            const itemId = menuItem.dataset.id;
            if (!itemId) return;
            
            // Show quantity controls
            const quantityControls = menuItem.querySelector('.quantity-controls');
            if (!quantityControls) return;
            
            quantityControls.style.display = 'flex';
            this.style.display = 'none';
            
            // Initialize quantity
            const quantityDisplay = quantityControls.querySelector('.quantity');
            if (!quantityDisplay) return;
            
            quantityDisplay.textContent = '1';
            
            // Set up confirm button
            const confirmBtn = quantityControls.querySelector('.confirm-add');
            if (!confirmBtn) return;
            
            confirmBtn.onclick = function() {
                const quantity = parseInt(quantityDisplay.textContent);
                if (isNaN(quantity) || quantity < 1) return;
                
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
            if (quantityDisplay) {
                quantityDisplay.textContent = parseInt(quantityDisplay.textContent) + 1;
            }
        } else if (e.target.classList.contains('decrement')) {
            const quantityDisplay = e.target.parentElement.querySelector('.quantity');
            if (quantityDisplay) {
                const current = parseInt(quantityDisplay.textContent);
                if (current > 1) {
                    quantityDisplay.textContent = current - 1;
                }
            }
        }
    });
}

/* ======================
   CHECKOUT FUNCTIONALITY
   ====================== */
function initCheckoutForm() {
    const checkoutForm = document.getElementById('checkout-form');
    if (!checkoutForm) return;
    
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
        .then(handleResponse)
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

/* ======================
   CART OPERATIONS
   ====================== */
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
    .then(handleResponse)
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showToast('Item added to cart');
            
            // Refresh cart if sidebar is open
            const cartSidebar = document.getElementById('cart-sidebar');
            if (cartSidebar && cartSidebar.style.right === '0px') {
                loadCartItems();
            }
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
    .then(handleResponse)
    .then(data => {
        if (!data.success) {
            console.error('Failed to load cart:', data.error);
            return;
        }
        
        const cartItemsContainer = document.getElementById('cart-items');
        const totalAmountElement = document.getElementById('total-amount');
        const checkoutBtn = document.getElementById('checkout-btn');
        
        if (!cartItemsContainer || !totalAmountElement || !checkoutBtn) return;
        
        cartItemsContainer.innerHTML = '';
        
        if (data.items && data.items.length > 0) {
            let total = 0;
            
            data.items.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'cart-item';
                itemElement.innerHTML = `
                    <div class="cart-item-info">
                        <h4>${escapeHtml(item.name)}</h4>
                        <p>${item.quantity} × Ksh ${item.price.toFixed(2)}</p>
                        ${item.available ? '' : '<p class="stock-warning">Out of stock</p>'}
                    </div>
                    <div class="cart-item-total">
                        <p>Ksh ${item.subtotal.toFixed(2)}</p>
                        <button class="remove-item" data-id="${escapeHtml(item.id)}">×</button>
                    </div>
                    <div class="cart-item-actions">
                        <button class="decrease-item" data-id="${escapeHtml(item.id)}">-</button>
                        <button class="increase-item" data-id="${escapeHtml(item.id)}">+</button>
                    </div>
                `;
                cartItemsContainer.appendChild(itemElement);
                total += item.subtotal;
            });
            
            totalAmountElement.textContent = total.toFixed(2);
            checkoutBtn.style.display = 'block';
            
            // Add event listeners
            document.querySelectorAll('.remove-item').forEach(btn => {
                btn.addEventListener('click', () => removeFromCart(btn.dataset.id));
            });
            
            document.querySelectorAll('.decrease-item').forEach(btn => {
                btn.addEventListener('click', () => updateCartItem(btn.dataset.id, -1));
            });
            
            document.querySelectorAll('.increase-item').forEach(btn => {
                btn.addEventListener('click', () => updateCartItem(btn.dataset.id, 1));
            });
        } else {
            cartItemsContainer.innerHTML = '<p>Your cart is empty</p>';
            totalAmountElement.textContent = '0.00';
            checkoutBtn.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error loading cart:', error);
        showToast('Failed to load cart items');
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
    .then(handleResponse)
    .then(data => {
        if (data.success) {
            loadCartItems();
            updateCartCount();
        } else {
            alert(data.error || 'Error updating cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update cart item');
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
    .then(handleResponse)
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

function updateCartCount() {
    fetch('/get-cart-count/')
    .then(handleResponse)
    .then(data => {
        const cartCount = document.getElementById('cart-count');
        if (cartCount && data.cart_count !== undefined) {
            cartCount.textContent = data.cart_count;
        }
    })
    .catch(error => {
        console.error('Error updating cart count:', error);
    });
}

/* ======================
   UTILITY FUNCTIONS
   ====================== */
function handleResponse(response) {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
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