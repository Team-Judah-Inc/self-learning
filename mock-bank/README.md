# 🏦 Mock-Bank System

A professional, modular banking ecosystem designed for development, testing, and financial data simulation. This project bridges the gap between a RESTful API and a Statistical Simulation Engine.

## 🏗 System Architecture

The project is divided into two distinct domains to ensure high maintainability and clear separation of concerns:

1. Banking API (app/): A production-ready Flask server that handles authentication, authorization, and data delivery.
2. Data Generator (data_gen/): A sophisticated simulation engine that models human financial behavior using statistical distributions.



## 📂 Project Structure

Mock-Bank/
├── app/                    # Flask Application Factory
│   ├── routes/             # Blueprints (users, accounts, cards)
│   ├── auth.py             # JWT Decorator & security logic
│   ├── utils.py            # API-specific helpers
│   └── __init__.py         # App initialization & extension setup
├── data_gen/               # Simulation Engine Package
│   ├── config.py           # Financial rules, probabilities & profiles
│   ├── generators.py       # Logic for creating Users, Accounts, and Cards
│   ├── simulation.py       # The core "Time" and Transaction engine
│   └── utils.py            # File I/O, reporting, and ID management
├── mock_data/              # JSON repository (The "Database")
├── generate.py             # Interactive Terminal Dashboard (CLI)
├── run.py                  # API Entry Point
├── config.py               # Global API Environment Config
├── Dockerfile              # Containerization recipe
└── docker-compose.yml      # Multi-service orchestration (API + DB)

------------------------
## 🚀 Quick Start Guide

### 1. Environment Setup
Create and activate a virtual environment, then install dependencies:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### 2. Initialize the Banking World
You must generate a world before the API can serve data. Launch the Interactive Dashboard:
python generate.py
* Select [1]: To wipe existing data and create 5 initial users with 30 days of history.
* Select [2]: To evolve time (advance the world by X days to generate payroll and spending).



### 3. Start the API
python run.py
The API will be accessible at: http://127.0.0.1:5000

## 🔐 API Documentation & Auth

### Interactive Swagger UI
Explore the full API schema and test endpoints directly:
http://127.0.0.1:5000/apidocs/



### Authentication Flow
1. Login: POST /login with username and password.
2. Token: Retrieve the token from the JSON response.
3. Authorized Requests: Include the token in your headers:
   Authorization: Bearer <your_token>

## 📊 Simulation Logic & Mathematics

The system uses a Behavioral Simulation Model rather than simple random numbers.

### Spending Distribution
Discretionary spending is calculated using a Gaussian (Normal) Distribution. Each user profile (FRUGAL, AVERAGE, SPENDER) has a unique mean ($ \mu $) and standard deviation ($ \sigma $):

$$f(x | \mu, \sigma) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}$$

### Financial Rules
* Payroll: Salaries are deposited automatically on configured days (default: 1st and 15th).
* Credit Billing: Credit card debt is automatically settled from the linked Checking account on the user's specific billing_day.
* Double-Entry Transfers: Every transfer creates two atomic transaction records linked by a unique transfer_group_id.



## 🛠 Tech Stack

* Backend: Python / Flask
* Security: PyJWT, Flask-Limiter, Werkzeug
* Docs: Flasgger (OpenAPI/Swagger)
* Data: Faker, JSON-based persistence
* DevOps: Docker, Docker-Compose

## 📜 License
This project is licensed under the MIT License.