"""
Banking Simulation Engine Module.

This module contains the core simulation logic for generating realistic
banking data over time, including user creation, account management,
card transactions, and time-based events like payroll and billing.

Classes:
    BankingSimulation: Main simulation engine managing the banking world.

Functions:
    process_manual_transaction: Handle manual transaction requests.
    process_transfer: Execute inter-account transfers.
    run_simulation_loop: Advance simulation time and generate events.
"""

import datetime
import random
from typing import List, Optional, Dict, Any

from werkzeug.security import generate_password_hash

from .models import User, Account, Card
from .repository import DataRepository
from .config import (
    TransactionType,
    AccountType,
    AccountStatus,
    CardStatus,
    SpendingProfile,
    TransactionCategory
)
from .utils import fake, get_consistent_company, pick_weighted_category, pick_location


class BankingSimulation:
    """
    Core simulation engine for the banking system.
    
    Manages the creation of users, accounts, cards, and the generation
    of transactions over simulated time. Uses a repository for data
    persistence, allowing different storage backends.
    
    Attributes:
        repo: Data repository for persistence operations.
        config: Simulation configuration dictionary.
        metadata: Simulation state metadata (current date, etc.).
        users: In-memory cache of User objects.
        accounts: In-memory cache of Account objects.
        cards: In-memory cache of Card objects.
        account_txns: Buffer for account transactions pending save.
        card_txns: Buffer for card transactions pending save.
        
    Example:
        >>> repo = SqlRepository("sqlite:///bank.db")
        >>> sim = BankingSimulation(repo)
        >>> sim.load_world()
        >>> user = sim.create_user()
        >>> account = sim.create_account(user.user_id)
        >>> sim.save_world()
    """
    
    def __init__(self, repository: DataRepository) -> None:
        """
        Initialize the simulation engine.
        
        Args:
            repository: Data repository for persistence operations.
        """
        self.repo = repository
        self.config: Dict[str, Any] = self.repo.load_config()
        self.metadata: Dict[str, Any] = self.repo.load_metadata()
        
        # In-memory cache for creation operations
        self.users: List[User] = []
        self.accounts: List[Account] = []
        self.cards: List[Card] = []
        
        # Transaction buffers for batch saving
        self.account_txns: List[Dict[str, Any]] = []
        self.card_txns: List[Dict[str, Any]] = []

    # =========================================================================
    # World State Management
    # =========================================================================

    def load_world(self) -> None:
        """
        Load the full world state from the repository.
        
        Loads all users, accounts, and cards into memory and reconstructs
        the object relationships.
        
        Note:
            This is a legacy method kept for compatibility with initialization
            logic. The simulation loop uses batch processing instead.
        """
        self.metadata = self.repo.load_metadata()
        raw_users, raw_accounts, raw_cards, _, _ = self.repo.load_resources()
        self._rehydrate_models(raw_users, raw_accounts, raw_cards)

    def _rehydrate_models(
        self, 
        raw_users: List[Dict[str, Any]], 
        raw_accounts: List[Dict[str, Any]], 
        raw_cards: List[Dict[str, Any]]
    ) -> None:
        """
        Reconstruct object graph from raw dictionary data.
        
        Creates User, Account, and Card objects and establishes
        the relationships between them.
        
        Args:
            raw_users: List of user dictionaries.
            raw_accounts: List of account dictionaries.
            raw_cards: List of card dictionaries.
        """
        # Create User objects
        self.users = [User(u) for u in raw_users]
        
        # Create Account objects with owner references
        self.accounts = []
        for acc_data in raw_accounts:
            owner = self._find_user(acc_data['user_id'])
            if owner:
                self.accounts.append(Account(acc_data, owner, self))
        
        # Create Card objects with account references
        self.cards = []
        for card_data in raw_cards:
            account = self._find_account(card_data['account_id'])
            if account:
                self.cards.append(Card(card_data, account, self))

    def save_world(self) -> None:
        """
        Persist the current world state to the repository.
        
        Saves all users, accounts, cards, transactions, and metadata.
        Used primarily during initialization and manual operations.
        """
        self.repo.save_all(
            self.users, 
            self.accounts, 
            self.cards, 
            self.account_txns, 
            self.card_txns, 
            self.metadata
        )

    # =========================================================================
    # Entity Lookup
    # =========================================================================

    def _find_user(self, user_id: str) -> Optional[User]:
        """
        Find a user by ID in the in-memory cache.
        
        Args:
            user_id: The user's unique identifier.
            
        Returns:
            User object if found, None otherwise.
        """
        return next((u for u in self.users if u.user_id == user_id), None)

    def _find_account(self, account_id: str) -> Optional[Account]:
        """
        Find an account by ID in the in-memory cache.
        
        Args:
            account_id: The account's unique identifier.
            
        Returns:
            Account object if found, None otherwise.
        """
        return next((a for a in self.accounts if a.account_id == account_id), None)

    # =========================================================================
    # Transaction Recording
    # =========================================================================

    def record_account_txn(
        self, 
        account_id: str, 
        amount: float, 
        desc: str, 
        cat: str, 
        loc: str, 
        date: str, 
        type_override: Optional[str] = None, 
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an account transaction to the ledger.
        
        Creates a transaction record and adds it to the pending buffer.
        
        Args:
            account_id: The account's unique identifier.
            amount: Transaction amount (negative for debits).
            desc: Transaction description.
            cat: Transaction category.
            loc: Transaction location.
            date: ISO format date string.
            type_override: Force transaction type instead of inferring.
            group_id: Optional group ID for linked transactions.
            
        Returns:
            The created transaction record dictionary.
        """
        txn_id = self.repo.generate_id('atxn')
        txn_type = type_override or (
            TransactionType.DEBIT if amount < 0 else TransactionType.CREDIT
        )
        
        record = {
            "transaction_id": txn_id,
            "account_id": account_id,
            "amount": amount,
            "date": date,
            "description": desc,
            "category": cat,
            "location": loc,
            "type": txn_type
        }
        
        if group_id:
            record['transfer_group_id'] = group_id
            
        self.account_txns.append(record)
        return record

    def record_card_txn(
        self, 
        card_id: str, 
        amount: float, 
        desc: str, 
        cat: str, 
        loc: str, 
        date: str
    ) -> Dict[str, Any]:
        """
        Record a credit card transaction.
        
        Args:
            card_id: The card's unique identifier.
            amount: Transaction amount.
            desc: Transaction description.
            cat: Transaction category.
            loc: Transaction location.
            date: ISO format date string.
            
        Returns:
            The created transaction record dictionary.
        """
        txn_id = self.repo.generate_id('ctxn')
        
        record = {
            "transaction_id": txn_id,
            "card_id": card_id,
            "amount": amount,
            "date": date,
            "description": desc,
            "category": cat,
            "location": loc,
            "type": TransactionType.DEBIT
        }
        
        self.card_txns.append(record)
        return record

    # =========================================================================
    # Entity Creation
    # =========================================================================

    def create_user(self, overrides: Optional[Dict[str, Any]] = None) -> User:
        """
        Generate a new random user.
        
        Creates a user with fake personal data and adds them to the
        in-memory cache.
        
        Args:
            overrides: Optional dictionary of values to override defaults.
            
        Returns:
            The newly created User object.
            
        Example:
            >>> user = sim.create_user(overrides={"first_name": "John"})
            >>> print(user.first_name)
            'John'
        """
        uid = self.repo.generate_id('user', self.users)
        current_date = self.metadata.get(
            'current_date', 
            datetime.date.today().isoformat()
        )
        
        data = {
            "user_id": uid,
            "username": f"user{uid.split('_')[1]}",
            "password_hash": generate_password_hash(
                "password123", 
                method="pbkdf2:sha256"
            ),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "city": fake.city(),
            "created_at": current_date,
            "settings": {"theme": "light", "notifications": True}
        }
        
        if overrides:
            data.update(overrides)
            
        user = User(data)
        self.users.append(user)
        return user

    def create_account(
        self, 
        user_id: str, 
        overrides: Optional[Dict[str, Any]] = None
    ) -> Optional[Account]:
        """
        Create a bank account for an existing user.
        
        Args:
            user_id: The owning user's unique identifier.
            overrides: Optional dictionary of values to override defaults.
            
        Returns:
            The newly created Account object, or None if user not found.
            
        Example:
            >>> account = sim.create_account(user.user_id, 
            ...                              overrides={"balance": 5000.00})
        """
        user = self._find_user(user_id)
        if not user:
            return None
            
        aid = self.repo.generate_id('account', self.accounts)
        fin_config = self.config['financial']
        
        initial_balance = round(random.uniform(
            fin_config['initial_balance_range'][0], 
            fin_config['initial_balance_range'][1]
        ), 2)
        
        salary = random.randrange(
            fin_config['salary_range'][0], 
            fin_config['salary_range'][1], 
            100
        )
        
        data = {
            "account_id": aid,
            "user_id": user_id,
            "type": AccountType.CHECKING,
            "currency": "USD",
            "balance": initial_balance,
            "salary_amount": salary,
            "status": AccountStatus.ACTIVE
        }
        
        if overrides:
            data.update(overrides)
            
        account = Account(data, user, self)
        self.accounts.append(account)
        return account

    def create_card(
        self, 
        account_id: str, 
        overrides: Optional[Dict[str, Any]] = None
    ) -> Optional[Card]:
        """
        Issue a credit card linked to a bank account.
        
        Args:
            account_id: The linked account's unique identifier.
            overrides: Optional dictionary of values to override defaults.
            
        Returns:
            The newly created Card object, or None if account not found.
            
        Example:
            >>> card = sim.create_card(account.account_id,
            ...                        overrides={"limit": 10000})
        """
        account = self._find_account(account_id)
        if not account:
            return None
            
        cid = self.repo.generate_id('card', self.cards)
        fin_config = self.config['financial']
        time_config = self.config['time']
        behavior_config = self.config['behavior']
        
        current_date = self.metadata.get(
            'current_date', 
            datetime.date.today().isoformat()
        )
        curr_date = datetime.date.fromisoformat(current_date)
        
        expiry_years = time_config['card_expiry_years']
        expiry_date = curr_date + datetime.timedelta(days=365 * expiry_years)
        
        data = {
            "card_id": cid,
            "account_id": account_id,
            "masked_number": f"****-****-****-{random.randint(1000, 9999)}",
            "status": CardStatus.ACTIVE,
            "limit": fin_config['default_credit_limit'],
            "billing_day": random.choice(time_config['billing_cycle_options']),
            "spending_profile": random.choice(SpendingProfile.all()),
            "current_spend": 0.0,
            "issue_date": curr_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "last_bill_date": None
        }
        
        if overrides:
            data.update(overrides)
            
        card = Card(data, account, self)
        self.cards.append(card)
        return card


# =============================================================================
# Manual Transaction Processing
# =============================================================================

def process_manual_transaction(
    sim: BankingSimulation, 
    link_id: str, 
    overrides: Optional[Dict[str, Any]] = None
) -> None:
    """
    Handle a manual transaction request.
    
    Processes a transaction on either a card or account based on the
    link_id prefix.
    
    Args:
        sim: The BankingSimulation instance.
        link_id: Card ID (card_*) or Account ID (acc_*).
        overrides: Optional transaction parameters (amount, category, etc.).
        
    Example:
        >>> process_manual_transaction(sim, "acc_123", {"amount": -50.00})
    """
    config = sim.config
    default_amount = config['financial']['manual_transaction_default']
    amount = float(overrides.get('amount', default_amount)) if overrides else default_amount
    current_date = sim.metadata['current_date']

    if link_id.startswith("card_"):
        _process_manual_card_charge(sim, link_id, amount, current_date, overrides)
    elif link_id.startswith("acc_"):
        _process_manual_account_op(sim, link_id, amount, current_date, overrides)


def _process_manual_card_charge(
    sim: BankingSimulation, 
    card_id: str, 
    amount: float, 
    date: str, 
    overrides: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process a manual card charge.
    
    Args:
        sim: The BankingSimulation instance.
        card_id: The card's unique identifier.
        amount: Amount to charge.
        date: ISO format date string.
        overrides: Optional transaction parameters.
    """
    card = next((c for c in sim.cards if c.card_id == card_id), None)
    if not card:
        print(f"❌ Error: Card {card_id} not found")
        return

    category = (
        overrides.get('category', pick_weighted_category(sim.config)) 
        if overrides else pick_weighted_category(sim.config)
    )
    location = (
        overrides.get('location', pick_location(card.linked_account.owner.city, sim.config)) 
        if overrides else pick_location(card.linked_account.owner.city, sim.config)
    )

    txn = card.charge(amount, "Manual Swipe", category, location, date)
    
    if txn:
        print(f"💳 Charged. New Spend: {card.current_spend:.2f}")
    else:
        print("⛔ Declined: Limit Exceeded")


def _process_manual_account_op(
    sim: BankingSimulation, 
    account_id: str, 
    amount: float, 
    date: str, 
    overrides: Optional[Dict[str, Any]] = None
) -> None:
    """
    Process a manual account operation.
    
    Args:
        sim: The BankingSimulation instance.
        account_id: The account's unique identifier.
        amount: Amount to credit/debit.
        date: ISO format date string.
        overrides: Optional transaction parameters.
    """
    account = next((a for a in sim.accounts if a.account_id == account_id), None)
    if not account:
        print(f"❌ Error: Account {account_id} not found")
        return

    category = overrides.get('category', TransactionCategory.MISC) if overrides else TransactionCategory.MISC
    location = (
        overrides.get('location', pick_location(account.owner.city, sim.config)) 
        if overrides else pick_location(account.owner.city, sim.config)
    )

    account.post_transaction(amount, "Manual Op", category, location, date)
    print(f"💰 Balance Adjusted: {account.balance:.2f}")


# =============================================================================
# Transfer Processing
# =============================================================================

def process_transfer(
    sim: BankingSimulation, 
    sender_id: str, 
    receiver_id: str, 
    overrides: Optional[Dict[str, Any]] = None
) -> None:
    """
    Execute a money transfer between two accounts.
    
    Creates linked debit and credit transactions with a shared group ID.
    
    Args:
        sim: The BankingSimulation instance.
        sender_id: Source account ID.
        receiver_id: Destination account ID.
        overrides: Optional parameters (amount).
        
    Example:
        >>> process_transfer(sim, "acc_123", "acc_456", {"amount": 100.00})
    """
    sender = next((a for a in sim.accounts if a.account_id == sender_id), None)
    receiver = next((a for a in sim.accounts if a.account_id == receiver_id), None)
    
    if not sender or not receiver:
        print("❌ Invalid Accounts")
        return

    amount = abs(float(overrides.get('amount', 50.00)) if overrides else 50.00)
    
    # Generate a group ID to link the two sides of the transfer
    grp_id = f"grp_{sim.repo.generate_id('atxn', sim.account_txns).split('_')[1]}"
    date = sim.metadata['current_date']

    sender.post_transaction(
        -amount, 
        f"Transfer to {receiver_id}", 
        TransactionCategory.TRANSFER, 
        "Online", 
        date, 
        TransactionType.DEBIT, 
        grp_id
    )
    receiver.post_transaction(
        amount, 
        f"Transfer from {sender_id}", 
        TransactionCategory.TRANSFER, 
        "Online", 
        date, 
        TransactionType.CREDIT, 
        grp_id
    )
    
    print(f"✅ Transferred ${amount:.2f}")


# =============================================================================
# Simulation Loop
# =============================================================================

def run_simulation_loop(
    sim: BankingSimulation, 
    days: int = 0, 
    hours: int = 0, 
    minutes: float = 0, 
    process_only: bool = False
) -> Dict[str, Any]:
    """
    Advance the simulation clock and generate events.
    
    Processes time-based events like spending, payroll, and billing
    for all accounts in the system.
    
    Args:
        sim: The BankingSimulation instance.
        days: Number of days to advance.
        hours: Number of hours to advance.
        minutes: Number of minutes to advance.
        process_only: If True, skip random spending (for testing).
        
    Returns:
        Statistics dictionary with counts of generated events.
        
    Example:
        >>> stats = run_simulation_loop(sim, days=30)
        >>> print(f"Generated {stats['transactions_added']} transactions")
    """
    # Setup time range
    start_time = _parse_simulation_start_time(sim.metadata['current_date'])
    delta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
    end_time = start_time + delta
    
    print(f"⏳ Advancing {start_time} -> {end_time}...")

    stats = {"transactions_added": 0}
    
    # Clear transaction buffers for this batch
    sim.account_txns = []
    sim.card_txns = []

    # Process accounts in batches
    _process_all_account_batches(sim, start_time, end_time, process_only)

    # Finalize simulation
    _finalize_simulation(sim, end_time, stats)
    
    print("✅ Time Travel Complete.")
    return stats


def _parse_simulation_start_time(date_str: str) -> datetime.datetime:
    """
    Parse the simulation start time from a date string.
    
    Args:
        date_str: ISO format date or datetime string.
        
    Returns:
        datetime object representing the start time.
    """
    try:
        return datetime.datetime.fromisoformat(date_str)
    except ValueError:
        # Fallback for legacy date-only strings
        return datetime.datetime.fromisoformat(date_str + "T00:00:00")


def _process_all_account_batches(
    sim: BankingSimulation,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    process_only: bool
) -> None:
    """
    Process all accounts in batches to avoid memory issues.
    
    Args:
        sim: The BankingSimulation instance.
        start_time: Simulation start datetime.
        end_time: Simulation end datetime.
        process_only: If True, skip random spending.
    """
    BATCH_SIZE = 100
    offset = 0
    
    while True:
        # Fetch a batch of accounts
        raw_accounts = sim.repo.get_accounts_batch(limit=BATCH_SIZE, offset=offset)
        if not raw_accounts:
            break
        
        # Process this batch
        active_accounts = _hydrate_account_batch(sim, raw_accounts)
        _simulate_time_range(sim, active_accounts, start_time, end_time, process_only)
        
        offset += BATCH_SIZE


def _hydrate_account_batch(
    sim: BankingSimulation,
    raw_accounts: List[Dict[str, Any]]
) -> List[Account]:
    """
    Create Account objects from raw data with cards attached.
    
    Optimized to batch-fetch user cities and cards to avoid N+1 queries.
    
    Args:
        sim: The BankingSimulation instance.
        raw_accounts: List of account dictionaries.
        
    Returns:
        List of hydrated Account objects with cards attached.
    """
    # Batch fetch user cities
    user_ids = list(set(acc['user_id'] for acc in raw_accounts))
    city_map = sim.repo.get_user_city_map(user_ids)
    
    # Batch fetch cards for all accounts
    account_ids = [acc['account_id'] for acc in raw_accounts]
    cards_map = sim.repo.get_cards_batch(account_ids)
    
    active_accounts = []
    for acc_data in raw_accounts:
        # Create lightweight user with just the city
        user_city = city_map.get(acc_data['user_id'], 'Unknown')
        dummy_user = User({
            'user_id': acc_data['user_id'],
            'username': 'unknown',
            'password_hash': '',
            'first_name': '',
            'last_name': '',
            'email': '',
            'city': user_city,
            'created_at': '',
            'settings': {}
        })
        
        account = Account(acc_data, dummy_user, sim)
        
        # Attach cards from batch fetch
        raw_cards = cards_map.get(account.account_id, [])
        account.cards = [Card(c, account, sim) for c in raw_cards]
        
        active_accounts.append(account)
    
    return active_accounts


def _simulate_time_range(
    sim: BankingSimulation,
    accounts: List[Account],
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    process_only: bool
) -> None:
    """
    Simulate events for a batch of accounts over a time range.
    
    Args:
        sim: The BankingSimulation instance.
        accounts: List of Account objects to process.
        start_time: Start of simulation period.
        end_time: End of simulation period.
        process_only: If True, skip random spending.
    """
    current_time = start_time
    
    while current_time < end_time:
        step_size = _calculate_step_size(current_time, end_time)
        if step_size.total_seconds() == 0:
            break

        next_step = current_time + step_size
        is_new_day = next_step.date() > current_time.date()
        
        current_time = next_step
        date_str = current_time.isoformat()
        
        # Probability factor scales hourly probabilities to current step
        time_factor = step_size.total_seconds() / 3600.0
        
        _process_simulation_step(
            sim, accounts, current_time, date_str, 
            is_new_day, time_factor, process_only
        )


def _calculate_step_size(
    current: datetime.datetime, 
    end: datetime.datetime
) -> datetime.timedelta:
    """
    Calculate the appropriate time step for simulation.
    
    Uses 1-hour steps for efficiency, but smaller steps if less time remains.
    
    Args:
        current: Current simulation time.
        end: End simulation time.
        
    Returns:
        timedelta for the next step.
    """
    remaining = end - current
    if remaining >= datetime.timedelta(hours=1):
        return datetime.timedelta(hours=1)
    return remaining


def _process_simulation_step(
    sim: BankingSimulation, 
    accounts: List[Account], 
    current_time: datetime.datetime, 
    date_str: str, 
    is_new_day: bool, 
    time_factor: float, 
    process_only: bool
) -> None:
    """
    Process a single simulation time step for all accounts.
    
    Handles payroll, card spending, and billing events.
    
    Args:
        sim: The BankingSimulation instance.
        accounts: List of accounts to process.
        current_time: Current simulation datetime.
        date_str: ISO format date string.
        is_new_day: Whether this step crosses a day boundary.
        time_factor: Scaling factor for hourly probabilities.
        process_only: If True, skip random spending.
    """
    payroll_days = sim.config['time']['payroll_days']
    
    for account in accounts:
        # Process payroll on designated days
        if is_new_day and current_time.day in payroll_days:
            _process_payroll(account, payroll_days, date_str)

        # Process card events
        for card in getattr(account, 'cards', []):
            if not process_only:
                _process_card_spending(sim, card, account, date_str, time_factor)
            
            # Process billing on billing day
            if is_new_day and current_time.day == card.billing_day:
                card.pay_bill(date_str)


def _process_payroll(
    account: Account, 
    payroll_days: List[int], 
    date_str: str
) -> None:
    """
    Process payroll deposit for an account.
    
    Splits monthly salary across payroll days.
    
    Args:
        account: The account to credit.
        payroll_days: List of payroll days in the month.
        date_str: ISO format date string.
    """
    amount = account.salary_amount / len(payroll_days)
    company = get_consistent_company(account.user_id)
    account.post_transaction(
        amount, 
        f"Payroll - {company}", 
        TransactionCategory.INCOME, 
        "Direct Deposit", 
        date_str, 
        TransactionType.CREDIT
    )


def _process_card_spending(
    sim: BankingSimulation, 
    card: Card, 
    account: Account, 
    date_str: str, 
    time_factor: float
) -> None:
    """
    Simulate random card spending based on spending profile.
    
    Uses the card's spending profile to determine probability and
    amount of transactions.
    
    Args:
        sim: The BankingSimulation instance.
        card: The card to potentially charge.
        account: The linked account (for location).
        date_str: ISO format date string.
        time_factor: Scaling factor for hourly probabilities.
    """
    spending_profiles = sim.config['behavior']['spending_profiles']
    profile = spending_profiles.get(card.spending_profile, spending_profiles[SpendingProfile.AVERAGE])
    
    # Adjust probability based on time step
    step_probability = profile['prob'] * time_factor
    
    if random.random() < step_probability:
        raw_amount = random.gauss(profile['mean'], profile['std'])
        # Clamp amount between min and max
        amount = round(max(profile['min'], min(profile['max'], raw_amount)), 2)
        
        category = pick_weighted_category(sim.config)
        location = pick_location(account.owner.city, sim.config)
        company = fake.company()
        
        card.charge(-amount, company, category, location, date_str)


def _finalize_simulation(
    sim: BankingSimulation,
    end_time: datetime.datetime,
    stats: Dict[str, Any]
) -> None:
    """
    Finalize the simulation by saving state and updating stats.
    
    Args:
        sim: The BankingSimulation instance.
        end_time: The new current simulation time.
        stats: Statistics dictionary to update.
    """
    # Update metadata with new current time
    sim.metadata['current_date'] = end_time.isoformat()
    sim.repo.save_metadata(sim.metadata)
    
    # Save generated transactions
    if sim.account_txns or sim.card_txns:
        sim.repo.save_transactions(sim.account_txns, sim.card_txns)
        stats['transactions_added'] = len(sim.account_txns) + len(sim.card_txns)
