document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity controls
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const menuItem = this.closest('.menu-item');
            const quantityControls = menuItem.querySelector('.quantity-controls');
            const addButton = menuItem.querySelector('.add-to-cart');
            
            addButton.style.display = 'none';
            quantityControls.style.display = 'flex';
            
            // Set up increment/decrement buttons
            const incrementBtn = quantityControls.querySelector('.increment');
            const decrementBtn = quantityControls.querySelector('.decrement');
            const quantityDisplay = quantityControls.querySelector('.quantity');
            const confirmBtn = quantityControls.querySelector('.confirm-add');
            
            let quantity = 1;
            
            incrementBtn.addEventListener('click', function() {
                quantity++;
                quantityDisplay.textContent = quantity;
            });
            
            decrementBtn.addEventListener('click', function() {
                if (quantity > 1) {
                    quantity--;
                    quantityDisplay.textContent = quantity;
                }
            });
            
            confirmBtn.addEventListener('click', function() {
                addToCart(menuItem.dataset.id, quantity);
                addButton.style.display = 'block';
                quantityControls.style.display = 'none';
            });
        });
    });
    
    // Checkout button
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            const checkoutModal = document.getElementById('checkout-modal');
            checkoutModal.style.display = 'flex';
        });
    }
    
    // Close modal
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Checkout form
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const phone = document.getElementById('phone').value;
            
            if (!/^2547\d{8}$/.test(phone)) {
                alert('Please enter a valid M-Pesa phone number (e.g., 2547XXXXXXXX)');
                return;
            }
            
            fetch('/checkout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    phone_number: phone
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.error) {
                    alert(data.error);
                }
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
        if (data.status === 'success') {
            updateCartCount();
            
            // If cart sidebar is open, refresh it
            const cartSidebar = document.getElementById('cart-sidebar');
            if (cartSidebar.style.right === '0px') {
                loadCartItems();
            }
        } else {
            alert(data.message || 'Error adding to cart');
        }
    });
}