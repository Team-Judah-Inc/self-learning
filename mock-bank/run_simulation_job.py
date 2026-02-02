"""
Simulation Job Runner.

This script runs the banking simulation as a standalone job, suitable for
cron jobs, Kubernetes CronJobs, or background task execution.

The job performs the following steps:
1. Initialize the repository based on configuration.
2. Check if the world is empty and seed initial data if needed.
3. Advance the simulation by the configured time interval.

Usage:
    python run_simulation_job.py

Environment Variables:
    DB_TYPE: Database type ('sqlite' or 'json').
    DATABASE_URL: SQLAlchemy database URL.
    SIMULATION_INTERVAL_SECONDS: Time to advance per job run (default: 3600).
"""

import sys
import datetime
import logging
from typing import Optional

from config import Config
from data_gen import BankingSimulation, SqlRepository, JsonRepository, run_simulation_loop
from data_gen.repository import DataRepository


# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Repository Factory
# =============================================================================

def create_repository() -> DataRepository:
    """
    Create the appropriate repository based on configuration.
    
    Reads DB_TYPE from Config and instantiates either SqlRepository
    or JsonRepository accordingly.
    
    Returns:
        DataRepository instance configured for the current environment.
        
    Example:
        >>> repo = create_repository()
        >>> isinstance(repo, (SqlRepository, JsonRepository))
        True
    """
    db_type = Config.DB_TYPE.lower()
    
    if db_type == 'sqlite' or 'sql' in db_type:
        logger.info(f"Using SQL Repository ({Config.SQLALCHEMY_DATABASE_URI})")
        return SqlRepository(Config.SQLALCHEMY_DATABASE_URI)
    else:
        logger.info(f"Using JSON Repository ({Config.DATA_DIR})")
        return JsonRepository(Config.DATA_DIR)


# =============================================================================
# World Initialization
# =============================================================================

def check_world_empty(bank: BankingSimulation) -> bool:
    """
    Check if the simulation world has any data.
    
    Args:
        bank: The BankingSimulation instance.
        
    Returns:
        True if the world is empty (no accounts), False otherwise.
    """
    accounts = bank.repo.get_all_accounts()
    return len(accounts) == 0


def seed_initial_users(bank: BankingSimulation, count: int = 5) -> None:
    """
    Create initial seed users with accounts and cards.
    
    Args:
        bank: The BankingSimulation instance.
        count: Number of users to create (default: 5).
    """
    logger.info(f"Creating {count} seed users...")
    
    for i in range(count):
        user = bank.create_user()
        account = bank.create_account(user.user_id)
        bank.create_card(account.account_id)
        logger.debug(f"Created user {i + 1}/{count}: {user.user_id}")


def generate_initial_history(bank: BankingSimulation, days: int = 30) -> None:
    """
    Generate initial transaction history.
    
    Runs the simulation for a specified number of days to create
    realistic historical data.
    
    Args:
        bank: The BankingSimulation instance.
        days: Number of days of history to generate (default: 30).
    """
    logger.info(f"Generating {days} days of initial history...")
    run_simulation_loop(bank, days=days)
    logger.info("Initial history generation complete.")


def initialize_world(bank: BankingSimulation) -> None:
    """
    Initialize the simulation world if it's empty.
    
    Checks if the world has any data. If empty, seeds initial users
    and generates historical transaction data.
    
    Args:
        bank: The BankingSimulation instance.
    """
    if check_world_empty(bank):
        logger.warning("⚠️ World is empty. Initializing new world...")
        
        # Set initial date
        bank.metadata['current_date'] = datetime.date.today().isoformat()
        
        # Create seed data
        seed_initial_users(bank, count=5)
        
        # Save the initial seed data
        bank.save_world()
        
        # Generate historical data
        generate_initial_history(bank, days=30)
        
        logger.info("✅ World initialized with seed data.")
    else:
        # Ensure metadata is loaded for existing world
        bank.metadata = bank.repo.load_metadata()
        logger.info("Existing world loaded successfully.")


# =============================================================================
# Simulation Execution
# =============================================================================

def calculate_simulation_duration(seconds: int) -> tuple[int, int, float]:
    """
    Convert seconds to days, hours, and minutes.
    
    Args:
        seconds: Total seconds to convert.
        
    Returns:
        Tuple of (days, hours, minutes).
    """
    days = seconds // 86400
    remaining = seconds % 86400
    hours = remaining // 3600
    minutes = (remaining % 3600) / 60.0
    
    return days, hours, minutes


def run_simulation_step(bank: BankingSimulation, seconds: int) -> Optional[dict]:
    """
    Run a single simulation step for the specified duration.
    
    Args:
        bank: The BankingSimulation instance.
        seconds: Number of seconds to advance the simulation.
        
    Returns:
        Statistics dictionary from the simulation, or None on error.
    """
    days, hours, minutes = calculate_simulation_duration(seconds)
    
    # Log the advancement
    if days > 0:
        logger.info(f"⏳ Advancing simulation by {days} days, {hours} hours, {minutes:.1f} minutes...")
    elif hours > 0:
        logger.info(f"⏳ Advancing simulation by {hours} hours, {minutes:.1f} minutes...")
    else:
        logger.info(f"⏳ Advancing simulation by {minutes:.1f} minutes ({seconds} seconds)...")
    
    # Run the simulation
    stats = run_simulation_loop(bank, days=days, hours=hours, minutes=minutes)
    
    return stats


def log_simulation_stats(stats: Optional[dict]) -> None:
    """
    Log simulation statistics.
    
    Args:
        stats: Statistics dictionary from run_simulation_loop.
    """
    if stats:
        txn_count = stats.get('transactions_added', 0)
        logger.info(f"📊 Stats: {txn_count} new transactions generated.")
    else:
        logger.warning("No statistics returned from simulation.")


# =============================================================================
# Main Job Entry Point
# =============================================================================

def run_job() -> None:
    """
    Main execution logic for the simulation job.
    
    Orchestrates the complete job workflow:
    1. Create repository
    2. Initialize simulation
    3. Initialize world if needed
    4. Run simulation step
    5. Log results
    """
    logger.info("🚀 Starting Banking Simulation Job...")
    
    # 1. Create repository and simulation
    repo = create_repository()
    bank = BankingSimulation(repo)
    
    # 2. Initialize world if needed
    initialize_world(bank)
    
    # 3. Run simulation step
    seconds = Config.SIMULATION_INTERVAL_SECONDS
    stats = run_simulation_step(bank, seconds)
    
    # 4. Log results
    log_simulation_stats(stats)
    
    logger.info("✅ Job Complete.")


# =============================================================================
# Script Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        run_job()
    except KeyboardInterrupt:
        logger.warning("Job interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)
