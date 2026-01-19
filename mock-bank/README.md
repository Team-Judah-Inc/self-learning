# 🏦 Mock-Bank System V4.0

A professional, modular banking ecosystem designed for development, testing, and financial data simulation. This project bridges the gap between a RESTful API and a Statistical Simulation Engine, now with robust SQL support and optimized data access.

## 🏗 System Architecture

The project is divided into three distinct domains to ensure high maintainability and clear separation of concerns:

1.  **Banking API (`app/`)**: A production-ready Flask server that handles authentication, authorization, and data delivery. It uses a **Repository Pattern** to abstract data access, supporting both SQL databases and JSON files.
2.  **Data Generator (`data_gen/`)**: A sophisticated simulation engine that models human financial behavior using statistical distributions. It generates realistic transaction histories, payrolls, and bill payments.
3.  **Simulation Job (`run_simulation_job.py`)**: An automated script designed to run as a scheduled job (e.g., Cron) to evolve the simulation over time.

## 📂 Project Structure

```
Mock-Bank/
├── app/                    # Flask Application Factory
│   ├── routes/             # API Blueprints (users, accounts, cards)
│   ├── auth.py             # JWT Decorator & security logic
│   ├── repository.py       # Data Access Layer (SQL & JSON implementations)
│   ├── utils.py            # API-specific helpers
│   └── __init__.py         # App initialization & extension setup
├── data_gen/               # Simulation Engine Package
│   ├── config.py           # Financial rules, probabilities & profiles
│   ├── generators.py       # Logic for creating Users, Accounts, and Cards
│   ├── simulation.py       # The core "Time" and Transaction engine
│   ├── sql_models.py       # SQLAlchemy Database Models
│   └── repository.py       # Data persistence logic for the generator
├── mock_data/              # Data storage (SQLite DB or JSON files)
├── generate.py             # Interactive Terminal Dashboard (CLI)
├── run.py                  # API Entry Point
├── run_simulation_job.py   # Automated Simulation Script
├── config.py               # Global API Environment Config
├── Dockerfile              # Containerization recipe
└── docker-compose.yml      # Multi-service orchestration
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Create and activate a virtual environment, then install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize the Banking World
You must generate a world before the API can serve data. Launch the Interactive Dashboard:
```bash
python generate.py
```
*   Select **[1]**: To wipe existing data and create 5 initial users with 30 days of history.
*   Select **[2]**: To evolve time manually (Advance by Days or Hours).
*   Select **[4]**: To manually create users, accounts, or transactions.

### 3. Start the API
```bash
python run.py
```
The API will be accessible at: `http://127.0.0.1:5000`

### 4. Automated Simulation (Optional)
To run the simulation as a background job (e.g., daily update):
```bash
python run_simulation_job.py
```

---

## 🔐 API Documentation & Auth

### Interactive Swagger UI
Explore the full API schema and test endpoints directly:
`http://127.0.0.1:5000/apidocs/`

### Authentication Flow
1.  **Login**: `POST /login` with username and password.
    *   Default password for generated users is `password123`.
    *   You can find usernames in the database or via the CLI stats.
2.  **Token**: Retrieve the token from the JSON response.
3.  **Authorized Requests**: Include the token in your headers:
    `Authorization: Bearer <your_token>`

---

## 📊 Simulation Logic & Configuration

The system uses a Behavioral Simulation Model driven by configuration.

### Spending Probabilities
Defined in `data_gen/config.py`, spending profiles determine how often a user makes a transaction **per hour**.

```python
"behavior": {
    "spending_profiles": {
        "FRUGAL":  {"prob": 0.01, ...}, # 1% chance per hour
        "AVERAGE": {"prob": 0.05, ...}, # 5% chance per hour
        "SPENDER": {"prob": 0.15, ...}  # 15% chance per hour
    }
}
```

### Financial Rules
*   **Payroll**: Salaries are deposited automatically on the 1st and 15th of the month.
*   **Credit Billing**: Credit card debt is automatically settled from the linked Checking account on the user's specific billing day.
*   **Hourly Simulation**: The engine evaluates spending opportunities every simulated hour, ensuring realistic transaction distribution.

---

## 🛠 Tech Stack

*   **Backend**: Python / Flask
*   **Database**: SQLite (via SQLAlchemy) with JSON fallback
*   **Security**: PyJWT, Flask-Limiter, Werkzeug
*   **Docs**: Flasgger (OpenAPI/Swagger)
*   **Data**: Faker, Gaussian Distributions
*   **DevOps**: Docker, Docker-Compose

## 📜 License
This project is licensed under the MIT License.