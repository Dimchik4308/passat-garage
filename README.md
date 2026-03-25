# 🚗 Passat Garage - E-commerce & Telegram Bot Integration

A full-stack e-commerce web application for auto parts, seamlessly integrated with a Telegram bot for real-time notifications. This pet project was developed to showcase solid backend development, database design, and asynchronous programming skills.

## 🚀 Key Features

* **E-commerce Core:** Full product catalog, detailed product pages, shopping cart, and checkout system.
* **Asynchronous Telegram Bot:** Integrated bot that sends instant notifications to subscribed users when new products are added.
* **Background Tasks:** Uses FastAPI `BackgroundTasks` to handle Telegram API broadcasting without blocking the main web server.
* **Responsive UI:** Custom dark-themed design built with HTML5, CSS3, and Jinja2 templates, fully optimized for mobile devices.

## 🛠 Tech Stack

* **Language:** Python 3
* **Web Frameworks:** Flask (Main App), FastAPI (Notification API)
* **Telegram Bot:** aiogram 3.x
* **Database & ORM:** SQLite, SQLAlchemy
* **Frontend:** HTML5, CSS3, Jinja2

## 🏗 Architecture Overview

This project uses a hybrid architecture to efficiently handle both synchronous web requests and asynchronous bot operations:
1. **Flask** serves the main web application, handles user sessions, and interacts with the database.
2. **FastAPI** provides an internal API endpoint. When an admin adds a new product, Flask sends a request to FastAPI.
3. **FastAPI BackgroundTasks** triggers the **aiogram** bot to broadcast messages to all Telegram subscribers asynchronously, ensuring the web interface remains fast and responsive.

## 💻 Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the repository
```bash
git clone [https://github.com/Dimchik4308/passat-garage.git](https://github.com/Dimchik4308/passat-garage.git)
cd passat-garage