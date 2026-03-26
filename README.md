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
git clone https://github.com/Dimchik4308/passat-garage.git
cd passat-garage
```

### 2. Set up a virtual environment
It is highly recommended to use a virtual environment to manage project dependencies.
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
Install all required libraries using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory of the project to securely store your credentials. Add the following variables:
```env
BOT_TOKEN=your_telegram_bot_token_here
FLASK_SECRET_KEY=your_super_secret_flask_key
BASE_URL=http://127.0.0.1:5000
```
*(Make sure not to commit your `.env` file to version control. It should be added to `.gitignore`)*

### 5. Initialize the Database
Before running the app, you need to create the SQLite database tables. 
```bash
# If using Flask-Migrate:
flask db upgrade

# OR, if running via python shell:
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 6. Run the Application
Because of the hybrid architecture, you need to run the Web Server and the Bot API Server simultaneously in two separate terminal windows.

**Terminal 1 (Run Flask Web App):**
```bash
python app.py
```
*The website will be available at `http://127.0.0.1:5000`*

**Terminal 2 (Run FastAPI & Telegram Bot):**
```bash
uvicorn bot_prod:app --reload
```
*The notification API will run on `http://127.0.0.1:8000`*

## 👨‍💻 Author
**Dimchik4308**
* Junior Python Developer
* GitHub: [@Dimchik4308](https://github.com/Dimchik4308)