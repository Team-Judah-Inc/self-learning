"""
Data Generation Package for Mock Banking Simulation.
"""
from .simulation import (
    BankingSimulation, 
    run_simulation_loop,
    process_manual_transaction,
    process_transfer
)
from .repository import JsonRepository, SqlRepository
from .config import DATA_DIR
from .models import User, Account, Card

__version__ = "4.0.0"