import os

DATA_DIR = 'mock_data'
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "probabilities": {
        "home_location_chance": 0.90,
        "categories": {
            "Food & Dining": 0.30, "Shopping": 0.20, "Transport": 0.15,
            "Entertainment": 0.10, "Health & Wellness": 0.10, "Other": 0.05, "Utilities": 0.10
        }
    },
    "financial": {
        "initial_balance_range": [1000, 5000], "salary_range": [3000, 9000],
        "default_credit_limit": 5000, "manual_transaction_default": -10.00,
        "transfer_default_amount": 50.00
    },
    "time": {
        "payroll_days": [1, 15], "billing_cycle_options": [1, 10, 15], "card_expiry_years": 3
    },
    "behavior": {
        "spending_profiles": {
            # Probabilities are now PER HOUR (0.0 - 1.0)
            # e.g., 0.05 = 5% chance per hour to make a transaction
            "FRUGAL":  {"prob": 0.01, "mean": 15.00,  "std": 5.00,  "min": 2.00,  "max": 60.00},
            "AVERAGE": {"prob": 0.05, "mean": 45.00,  "std": 20.00, "min": 5.00,  "max": 200.00},
            "SPENDER": {"prob": 0.15, "mean": 120.00, "std": 80.00, "min": 10.00, "max": 800.00}
        }
    }
}