# E-Commerce-using-FastApi

This is a backend system for an e-commerce platform built using FastAPI, SQLAlchemy, and PostgreSQL. It includes user authentication, product management, cart functionality, orders, and checkout.

## Features

- User Authentication (Signup, Login, JWT Tokens)
- Role-based access (Admin & User)
- Product Management (Add/Edit/Delete/View products)
- Cart Management (Add/Update/Remove/View items)
- Order Management (View history, Order details)
- Checkout with stock validation and order creation
- Logging and input validation

## Project Structure

app/
├── auth/ # User authentication
├── products/ # Product models and routes
├── cart/ # Cart-related APIs
├── orders/ # Orders and Checkout
├── core/ # Database, settings, dependencies
├── utils/ # Utility functions (e.g., email)
└── main.py # FastAPI app entry point


## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PrasangJhawar/E-Commerce-using-FastApi.git
   cd ecommerce-backend

2. **Create and activate virtual environment**
    python -m venv env
    source env/bin/activate  # on Windows: .\env\Scripts\activate

3. **Install dependencies**
    pip install -r requirements.txt

4. **Set up environment variables**
    create a .env file or configure app/core/config.py

5. **Run the app**
    uvicorn app.main:app --reload



**API Endpoints**
Explore API using the built-in Swagger docs:
    http://localhost:8000/docs

Some example endpoints:

- POST /auth/signup — Register new user
- POST /auth/signin — Login user
- GET /products/ — List public products
- POST /cart/ — Add product to cart
- GET /orders/ — Get order history
- POST /checkout/ — Place an order