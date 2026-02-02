"""
Utility Functions for Banking Simulation.

This module provides helper functions for data generation, including
random data generation, weighted category selection, and location picking.

Functions:
    get_consistent_company: Generate a stable company name for a user.
    pick_weighted_category: Select a transaction category based on probabilities.
    pick_location: Determine transaction location with home city bias.
"""

import random
from typing import Dict, Any

from faker import Faker


# Initialize Faker with a seed for reproducible test data
fake = Faker()
Faker.seed(12345)


def get_consistent_company(user_id: str) -> str:
    """
    Generate a stable company name based on the user ID.
    
    Uses the user ID as a seed to ensure the same user always gets
    the same employer name across simulation runs.
    
    Args:
        user_id: The user's unique identifier (format: "u_{number}_...").
        
    Returns:
        A company name string (e.g., "Acme Corp LLC").
        
    Example:
        >>> get_consistent_company("u_12345_1")
        'Johnson-Smith and Sons'
        >>> # Same input always produces same output
        >>> get_consistent_company("u_12345_1")
        'Johnson-Smith and Sons'
    """
    try:
        # Extract numeric portion from user_id for seeding
        seed_val = int(user_id.split('_')[1])
    except (ValueError, IndexError):
        # Fallback to hash if user_id format is unexpected
        seed_val = hash(user_id)
    
    # Create a temporary Faker instance with user-specific seed
    temp_fake = Faker()
    temp_fake.seed_instance(seed_val)
    
    return f"{temp_fake.company()} {temp_fake.company_suffix()}"


def pick_weighted_category(config: Dict[str, Any]) -> str:
    """
    Select a transaction category based on configured probabilities.
    
    Uses weighted random selection to pick a category, with weights
    defined in the configuration's probabilities.categories section.
    
    Args:
        config: Configuration dictionary containing probabilities.categories.
        
    Returns:
        Selected category string (e.g., "Food & Dining", "Shopping").
        
    Example:
        >>> config = {
        ...     "probabilities": {
        ...         "categories": {
        ...             "Food & Dining": 0.30,
        ...             "Shopping": 0.20,
        ...             "Transport": 0.15
        ...         }
        ...     }
        ... }
        >>> category = pick_weighted_category(config)
        >>> category in ["Food & Dining", "Shopping", "Transport"]
        True
    """
    categories_dict = config['probabilities']['categories']
    categories = list(categories_dict.keys())
    weights = list(categories_dict.values())
    
    return random.choices(categories, weights=weights, k=1)[0]


def pick_location(home_city: str, config: Dict[str, Any]) -> str:
    """
    Determine the location for a transaction.
    
    With high probability (configured), returns the user's home city.
    Otherwise, generates a random city to simulate travel or online purchases.
    
    Args:
        home_city: The user's home city.
        config: Configuration dictionary containing probabilities.home_location_chance.
        
    Returns:
        City name string for the transaction location.
        
    Example:
        >>> config = {"probabilities": {"home_location_chance": 0.90}}
        >>> # 90% chance to return "New York", 10% chance for random city
        >>> location = pick_location("New York", config)
    """
    home_chance = config['probabilities']['home_location_chance']
    
    if random.random() < home_chance:
        return home_city
    
    return fake.city()


def generate_masked_card_number() -> str:
    """
    Generate a masked credit card number.
    
    Returns:
        Masked card number string (format: "****-****-****-XXXX").
        
    Example:
        >>> number = generate_masked_card_number()
        >>> number.startswith("****-****-****-")
        True
    """
    last_four = random.randint(1000, 9999)
    return f"****-****-****-{last_four}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        The clamped value.
        
    Example:
        >>> clamp(150, 0, 100)
        100
        >>> clamp(-10, 0, 100)
        0
        >>> clamp(50, 0, 100)
        50
    """
    return max(min_val, min(max_val, value))
