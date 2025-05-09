# 🍽️ SEKU MESSHALL Web Application

A Django-based food ordering web application for SEKU MESSHALL. Students can view menu items, add them to a cart, and place orders. Admins can manage menu availability and orders through a backend interface.

---

## 🔧 Features

- 🍲 Menu display page  
- 🛒 Shopping cart with item counter  
- ✅ Order confirmation system  
- 📩 User alerts and messages  
- 📅 Dynamic footer with current year  
- 🎨 Styled using CSS and Font Awesome icons  

---

## 📁 Project Structure

- food/
- ├── portal/
- │ ├── food_portal/
- │ │ ├── pycache/
- │ │ ├── init.py
- │ │ ├── asgi.py
- │ │ ├── settings.py
- │ │ ├── urls.py
- │ │ ├── wsgi.py
- │ ├── media/
- │ │ └── menu images/
- │ ├── menu/
- │ ├── db.sqlite3
- │ ├── manage.py
- │ └── README.md


## 📝 Installation and Setup
1. Clone the repository using `git clone https://github.com/your-username/sekum
2. Create a new database using `python manage.py migrate`
3. Run the application using `python manage.py runserver`
4. Access the application at `http://localhost:8000/`
5. Create a new user account using the registration form
6. Log in to the application using the credentials created in step 6
7. Access the menu display page by clicking on the "Menu" tab
8. Add items to the shopping cart by clicking on the "Add to Cart" button
9. Place an order by clicking on the "Place Order" button
10. Access the admin interface by logging in with admin credentials
11. Manage menu availability and orders through the admin interface by `python manage.py createsuperuser`

-

