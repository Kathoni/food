document.addEventListener('DOMContentLoaded', function () {
    initCartFunctionality();
    initMenuItems();
    initCheckoutForm();
});

// Cart Management Functions
function updateCartCount() {
    fetch('/get-cart-count/')
        .then(handleResponse)
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount && data.cart_count !== undefined) {
                cartCount.textContent = data.cart_count;
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

function loadCartItems() {
    fetch('/get-cart/')
        .then(handleResponse)
        .then(data => {
            const cartItemsContainer = document.getElementById('cart-items');
            const totalAmountElement = document.getElementById('total-amount');
            const checkoutBtn = document.getElementById('checkout-btn');

            if (!cartItemsContainer || !totalAmountElement || !checkoutBtn) return;

            cartItemsContainer.innerHTML = '';

            if (data.success && data.items.length > 0) {
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
                            <button class="remove-item" data-id="${item.id}">Remove</button>
                        </div>
                    `;
                    cartItemsContainer.appendChild(itemElement);
                    total += item.subtotal;
                });

                totalAmountElement.textContent = total.toFixed(2);
                checkoutBtn.style.display = 'block';

                document.querySelectorAll('.remove-item').forEach(btn => {
                    btn.addEventListener('click', () => removeFromCart(btn.dataset.id));
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

function addToCart(itemId, quantity = 1) {
    fetch('/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ item_id: itemId, quantity: quantity })
    })
    .then(handleResponse)
    .then(data => {
        if (data.success) {
            updateCartCount();
            showToast('Item added to cart');

            const cartSidebar = document.getElementById('cart-sidebar');
            if (cartSidebar && cartSidebar.style.right === '0px') {
                loadCartItems();
            }
        } else {
            showToast(data.error || 'Error adding to cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to add item to cart');
    });
}

function removeFromCart(itemId) {
    fetch('/remove-from-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(handleResponse)
    .then(data => {
        if (data.success) {
            updateCartCount();
            loadCartItems();
            showToast('Item removed from cart');
        } else {
            showToast(data.error || 'Error removing item');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to remove item');
    });
}

// Menu Items Functionality
function initMenuItems() {
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function () {
            const menuItem = this.closest('.menu-item');
            if (!menuItem) return;

            const itemId = menuItem.dataset.id;
            const quantityControls = menuItem.querySelector('.quantity-controls');
            const quantityDisplay = quantityControls?.querySelector('.quantity');
            const confirmBtn = quantityControls?.querySelector('.confirm-add');

            if (!itemId || !quantityControls || !quantityDisplay || !confirmBtn) return;

            quantityControls.style.display = 'flex';
            this.style.display = 'none';
            quantityDisplay.textContent = '1'; // Start with 1 instead of 0

            confirmBtn.onclick = () => {
                const quantity = parseInt(quantityDisplay.textContent);
                if (!isNaN(quantity) && quantity > 0) {
                    addToCart(itemId, quantity);
                }
                quantityControls.style.display = 'none';
                this.style.display = 'block';
            };
        });
    });

    // Quantity controls
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('increment')) {
            const quantityDisplay = e.target.parentElement.querySelector('.quantity');
            if (quantityDisplay) {
                quantityDisplay.textContent = parseInt(quantityDisplay.textContent) + 1;
            }
        } else if (e.target.classList.contains('decrement')) {
            const quantityDisplay = e.target.parentElement.querySelector('.quantity');
            if (quantityDisplay) {
                const current = parseInt(quantityDisplay.textContent);
                quantityDisplay.textContent = current > 1 ? current - 1 : 1;
            }
        }
    });
}

// Checkout Functionality
function initCheckoutForm() {
    const checkoutForm = document.getElementById('checkout-form');
    if (!checkoutForm) return;

    checkoutForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email')?.value.trim() || '';
        const phone = document.getElementById('phone')?.value.trim() || '';

        if (!name) {
            showToast('Please enter your name');
            return;
        }

        // Show loading state
        const submitBtn = checkoutForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        fetch('/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ 
                name: name,
                email: email,
                phone: phone
            })
        })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                // Clear cart and redirect
                window.location.href = `/order/${data.order_id}/`;
            } else {
                showToast(data.error || 'Error processing your order');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred while processing your order');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

// Cart UI Functionality
function initCartFunctionality() {
    const cartLink = document.getElementById('cart-link');
    const cartSidebar = document.getElementById('cart-sidebar');
    const checkoutBtn = document.getElementById('checkout-btn');
    const checkoutModal = document.getElementById('checkout-modal');
    const closeModal = document.querySelector('.close-modal');

    // Toggle cart sidebar
    if (cartLink && cartSidebar) {
        cartLink.addEventListener('click', function (e) {
            e.preventDefault();
            cartSidebar.style.right = cartSidebar.style.right === '0px' ? '-350px' : '0px';
            if (cartSidebar.style.right === '0px') loadCartItems();
        });

        // Close sidebar when clicking outside
        document.addEventListener('click', function (e) {
            if (!cartSidebar.contains(e.target) && e.target !== cartLink && !cartLink.contains(e.target)) {
                cartSidebar.style.right = '-350px';
            }
        });
    }

    // Checkout modal handling
    if (checkoutBtn && checkoutModal) {
        checkoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            checkoutModal.style.display = 'block';
        });
    }

    if (closeModal && checkoutModal) {
        closeModal.addEventListener('click', function () {
            checkoutModal.style.display = 'none';
        });
    }

    window.addEventListener('click', function (e) {
        if (e.target === checkoutModal) {
            checkoutModal.style.display = 'none';
        }
    });

    updateCartCount();
}

// Utility Functions
function handleResponse(response) {
    if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
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