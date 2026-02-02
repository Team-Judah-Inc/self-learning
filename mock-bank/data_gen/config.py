"""
Data Generation Configuration Module.

This module contains all configuration constants, type definitions, and default
settings for the banking simulation data generation system.

Constants:
    DATA_DIR: Directory path for storing generated data files.
    DEFAULT_CONFIG: Default configuration dictionary for simulation parameters.

Type Classes:
    TransactionType: Constants for transaction types (DEBIT, CREDIT).
    AccountStatus: Constants for account statuses (ACTIVE, INACTIVE, FROZEN).
    AccountType: Constants for account types (CHECKING, SAVINGS).
    CardStatus: Constants for card statuses (ACTIVE, BLOCKED, EXPIRED).
    SpendingProfile: Constants for spending behavior profiles.
"""

import os
from typing import Dict, List, Any


# =============================================================================
# Directory Configuration
# =============================================================================

DATA_DIR = 'mock_data'
"""Default directory for storing mock data files."""

os.makedirs(DATA_DIR, exist_ok=True)


# =============================================================================
# Type Constants (Replace Magic Strings)
# =============================================================================

class TransactionType:
    """
    Constants for transaction types.
    
    Attributes:
        DEBIT: Money leaving an account (negative balance impact).
        CREDIT: Money entering an account (positive balance impact).
    """
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class AccountStatus:
    """
    Constants for account statuses.
    
    Attributes:
        ACTIVE: Account is operational and can perform transactions.
        INACTIVE: Account is dormant but can be reactivated.
        FROZEN: Account is locked, no transactions allowed.
    """
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FROZEN = "FROZEN"


class AccountType:
    """
    Constants for account types.
    
    Attributes:
        CHECKING: Standard checking account for daily transactions.
        SAVINGS: Savings account with potential interest accrual.
    """
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class CardStatus:
    """
    Constants for credit card statuses.
    
    Attributes:
        ACTIVE: Card is operational and can be used for purchases.
        BLOCKED: Card is temporarily blocked (e.g., suspected fraud).
        EXPIRED: Card has passed its expiry date.
    """
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class SpendingProfile:
    """
    Constants for user spending behavior profiles.
    
    These profiles determine transaction frequency and amounts during simulation.
    
    Attributes:
        FRUGAL: Low spending frequency, small transaction amounts.
        AVERAGE: Moderate spending patterns.
        SPENDER: High spending frequency, larger transaction amounts.
    """
    FRUGAL = "FRUGAL"
    AVERAGE = "AVERAGE"
    SPENDER = "SPENDER"
    
    @classmethod
    def all(cls) -> List[str]:
        """Return all available spending profiles."""
        return [cls.FRUGAL, cls.AVERAGE, cls.SPENDER]


class TransactionCategory:
    """
    Constants for transaction categories.
    
    Attributes:
        FOOD_DINING: Restaurants, groceries, food delivery.
        SHOPPING: Retail purchases, online shopping.
        TRANSPORT: Gas, public transit, ride-sharing.
        ENTERTAINMENT: Movies, games, subscriptions.
        HEALTH_WELLNESS: Medical, pharmacy, gym.
        UTILITIES: Bills, internet, phone.
        INCOME: Salary, deposits, refunds.
        TRANSFER: Inter-account transfers.
        BILLS: Credit card payments, loan payments.
        OTHER: Miscellaneous transactions.
    """
    FOOD_DINING = "Food & Dining"
    SHOPPING = "Shopping"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    HEALTH_WELLNESS = "Health & Wellness"
    UTILITIES = "Utilities"
    INCOME = "Income"
    TRANSFER = "Transfer"
    BILLS = "Bills"
    OTHER = "Other"
    MISC = "Misc"


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    "probabilities": {
        "home_location_chance": 0.90,
        "categories": {
            TransactionCategory.FOOD_DINING: 0.30,
            TransactionCategory.SHOPPING: 0.20,
            TransactionCategory.TRANSPORT: 0.15,
            TransactionCategory.ENTERTAINMENT: 0.10,
            TransactionCategory.HEALTH_WELLNESS: 0.10,
            TransactionCategory.OTHER: 0.05,
            TransactionCategory.UTILITIES: 0.10
        }
    },
    "financial": {
        "initial_balance_range": [1000, 5000],
        "salary_range": [3000, 9000],
        "default_credit_limit": 5000,
        "manual_transaction_default": -10.00,
        "transfer_default_amount": 50.00
    },
    "time": {
        "payroll_days": [1, 15],
        "billing_cycle_options": [1, 10, 15],
        "card_expiry_years": 3
    },
    "behavior": {
        "spending_profiles": {
            # Probabilities are PER HOUR (0.0 - 1.0)
            # e.g., 0.05 = 5% chance per hour to make a transaction
            SpendingProfile.FRUGAL: {
                "prob": 0.01,
                "mean": 15.00,
                "std": 5.00,
                "min": 2.00,
                "max": 60.00
            },
            SpendingProfile.AVERAGE: {
                "prob": 0.05,
                "mean": 45.00,
                "std": 20.00,
                "min": 5.00,
                "max": 200.00
            },
            SpendingProfile.SPENDER: {
                "prob": 0.15,
                "mean": 120.00,
                "std": 80.00,
                "min": 10.00,
                "max": 800.00
            }
        }
    }
}
"""
Default configuration dictionary for the banking simulation.

Structure:
    probabilities:
        home_location_chance: Probability that a transaction occurs in user's home city.
        categories: Weighted probabilities for transaction categories.
    
    financial:
        initial_balance_range: [min, max] for new account balances.
        salary_range: [min, max] for monthly salary amounts.
        default_credit_limit: Default credit limit for new cards.
        manual_transaction_default: Default amount for manual transactions.
        transfer_default_amount: Default amount for transfers.
    
    time:
        payroll_days: Days of month when salary is deposited.
        billing_cycle_options: Possible billing days for credit cards.
        card_expiry_years: Years until card expiration from issue date.
    
    behavior:
        spending_profiles: Configuration for each spending profile type.
            prob: Hourly probability of making a transaction.
            mean: Average transaction amount.
            std: Standard deviation for transaction amounts.
            min: Minimum transaction amount.
            max: Maximum transaction amount.
"""


# =============================================================================
# Serialization Constants
# =============================================================================

EXCLUDED_SERIALIZATION_KEYS = frozenset([
    'owner',
    'linked_account', 
    'repo',
    'sim',
    '_sa_instance_state',
    'cards'  # Dynamically attached during simulation
])
"""Keys to exclude when serializing model objects to dictionaries."""


def clean_model_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a model object to a clean dictionary for serialization.
    
    Removes internal state and relationship references that shouldn't be
    persisted or serialized.
    
    Args:
        obj: A model object or dictionary to clean.
        
    Returns:
        A dictionary with excluded keys removed.
        
    Example:
        >>> user = User(data)
        >>> clean_dict = clean_model_dict(user)
        >>> # clean_dict won't have 'owner', 'sim', etc.
    """
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in EXCLUDED_SERIALIZATION_KEYS}
    
    result = {}
    for key, value in obj.__dict__.items():
        if key not in EXCLUDED_SERIALIZATION_KEYS:
            result[key] = value
    return result
