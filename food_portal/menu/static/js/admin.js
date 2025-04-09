document.addEventListener("DOMContentLoaded", function () {
    // Assume you load existing items on page load; for demo use update and create operations.
});

// Function to update a menu item via AJAX
function updateMenuItem(itemId, newPrice, newUnits) {
    fetch("/update-item/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
            id: itemId,
            price: newPrice,
            available_units: newUnits
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Optionally reload the menu items list here
    })
    .catch(error => {
        console.error("Error updating menu item:", error);
    });
}

// Function to create a new announcement via AJAX
function postAnnouncement() {
    const title = document.getElementById("announcement-title").value;
    const message = document.getElementById("announcement-message").value;

    fetch("/create-announcement/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ title: title, message: message })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Optionally reload announcements list here
    })
    .catch(error => {
        console.error("Error creating announcement:", error);
    });
}

// Utility function for extracting CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
