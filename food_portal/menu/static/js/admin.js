document.addEventListener('DOMContentLoaded', function() {
    // Update menu items
    document.querySelectorAll('.update-item').forEach(button => {
        button.addEventListener('click', function() {
            const menuItem = this.closest('.admin-menu-item');
            const itemId = menuItem.dataset.id;
            const price = menuItem.querySelector('.price-input').value;
            const units = menuItem.querySelector('.units-input').value;
            
            fetch('/update-item/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    item_id: itemId,
                    price: price,
                    units: units
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Item updated successfully!');
                } else {
                    alert(data.message || 'Error updating item');
                }
            });
        });
    });
    
    // Resolve stock alerts
    document.querySelectorAll('.resolve-alert').forEach(button => {
        button.addEventListener('click', function() {
            const alertId = this.dataset.id;
            
            fetch('/resolve-alert/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    alert_id: alertId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.closest('li').remove();
                } else {
                    alert(data.message || 'Error resolving alert');
                }
            });
        });
    });
    
    // New announcement modal
    const newAnnouncementBtn = document.getElementById('new-announcement-btn');
    const announcementModal = document.getElementById('announcement-modal');
    
    if (newAnnouncementBtn && announcementModal) {
        newAnnouncementBtn.addEventListener('click', function() {
            announcementModal.style.display = 'flex';
        });
    }
    
    // Close modal
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Announcement form
    const announcementForm = document.getElementById('announcement-form');
    if (announcementForm) {
        announcementForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const title = document.getElementById('title').value;
            const message = document.getElementById('message').value;
            
            fetch('/create-announcement/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    title: title,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Announcement created successfully!');
                    announcementModal.style.display = 'none';
                    announcementForm.reset();
                } else {
                    alert(data.message || 'Error creating announcement');
                }
            });
        });
    }
});

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