"""
Data Generation Package for Mock Banking Simulation.

This package provides all the components needed to generate realistic
banking data, including users, accounts, cards, and transactions.

Modules:
    config: Configuration constants and type definitions.
    models: Domain model classes (User, Account, Card).
    repository: Data persistence layer (JSON and SQL backends).
    simulation: Core simulation engine and event processing.
    sql_models: SQLAlchemy ORM models.
    utils: Utility functions for data generation.

Main Classes:
    BankingSimulation: Core simulation engine.
    JsonRepository: JSON file-based data storage.
    SqlRepository: SQL database storage.
    User, Account, Card: Domain model classes.

Main Functions:
    run_simulation_loop: Advance simulation time and generate events.
    process_manual_transaction: Handle manual transaction requests.
    process_transfer: Execute inter-account transfers.
"""

from .simulation import (
    BankingSimulation, 
    run_simulation_loop,
    process_manual_transaction,
    process_transfer
)
from .repository import JsonRepository, SqlRepository
from .config import (
    DATA_DIR,
    TransactionType,
    AccountStatus,
    AccountType,
    CardStatus,
    SpendingProfile,
    TransactionCategory,
    DEFAULT_CONFIG,
    clean_model_dict
)
from .models import User, Account, Card


__version__ = "4.0.0"

__all__ = [
    # Simulation
    'BankingSimulation',
    'run_simulation_loop',
    'process_manual_transaction',
    'process_transfer',
    
    # Repositories
    'JsonRepository',
    'SqlRepository',
    
    # Models
    'User',
    'Account', 
    'Card',
    
    # Config & Constants
    'DATA_DIR',
    'DEFAULT_CONFIG',
    'TransactionType',
    'AccountStatus',
    'AccountType',
    'CardStatus',
    'SpendingProfile',
    'TransactionCategory',
    'clean_model_dict',
]
