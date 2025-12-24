"""
Data Generation Package for Mock Banking Simulation.
This package handles the creation of users, financial products, 
and the simulation of time and transactions.
"""

from .utils import (
    load_data, 
    save_data, 
    read_balances
)

from .generators import (
    create_user, 
    create_account, 
    create_card
)

from .simulation import (
    simulate_days, 
    create_manual_transaction, 
    create_transfer_transaction
)

# Version of the data generator
__version__ = "2.0.0"