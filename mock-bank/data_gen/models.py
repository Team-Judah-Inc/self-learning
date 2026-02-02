"""
Domain Models for Banking Simulation.

This module defines the core domain entities used in the banking simulation:
User, Account, and Card. These models encapsulate both data and behavior
for their respective entities.

Classes:
    BaseModel: Abstract base class providing common serialization.
    User: Represents a bank customer.
    Account: Represents a bank account with transaction capabilities.
    Card: Represents a credit card linked to an account.
"""

from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from .simulation import BankingSimulation


class BaseModel:
    """
    Abstract base class for all domain models.
    
    Provides common functionality for serialization and representation.
    All domain models should inherit from this class.
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary representation.
        
        Returns:
            Dictionary containing all public attributes of the model.
            
        Note:
            This returns the raw __dict__, which may include references
            to other objects. Use clean_model_dict() from config for
            serialization-safe output.
        """
        return self.__dict__


class User(BaseModel):
    """
    Represents a bank customer in the simulation.
    
    A User is the top-level entity that owns accounts. Each user has
    personal information, authentication credentials, and preferences.
    
    Attributes:
        user_id: Unique identifier (format: "u_{timestamp}_{counter}").
        username: Login username for authentication.
        password_hash: Hashed password (never store plain text).
        first_name: User's first name.
        last_name: User's last name.
        email: User's email address.
        city: User's home city (used for transaction location simulation).
        created_at: ISO format date string of account creation.
        settings: Dictionary of user preferences (theme, notifications, etc.).
        
    Example:
        >>> user_data = {
        ...     "user_id": "u_1234567890_1",
        ...     "username": "johndoe",
        ...     "password_hash": "pbkdf2:sha256:...",
        ...     "first_name": "John",
        ...     "last_name": "Doe",
        ...     "email": "john@example.com",
        ...     "city": "New York",
        ...     "created_at": "2024-01-15",
        ...     "settings": {"theme": "dark"}
        ... }
        >>> user = User(user_data)
    """
    
    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize a User from a dictionary.
        
        Args:
            data: Dictionary containing all user attributes.
                  Required keys: user_id, username, password_hash,
                  first_name, last_name, email, city, created_at, settings.
        """
        self.user_id: str = data['user_id']
        self.username: str = data['username']
        self.password_hash: str = data['password_hash']
        self.first_name: str = data['first_name']
        self.last_name: str = data['last_name']
        self.email: str = data['email']
        self.city: str = data['city']
        self.created_at: str = data['created_at']
        self.settings: Dict[str, Any] = data['settings']
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"User(id={self.user_id}, username={self.username})"


class Account(BaseModel):
    """
    Represents a bank account in the simulation.
    
    An Account belongs to a User and can have multiple Cards linked to it.
    It tracks balance, handles transactions, and manages payroll deposits.
    
    Attributes:
        account_id: Unique identifier (format: "acc_{timestamp}_{counter}").
        user_id: ID of the owning user.
        type: Account type (CHECKING, SAVINGS).
        currency: Currency code (e.g., "USD").
        balance: Current account balance.
        salary_amount: Monthly salary for payroll simulation.
        status: Account status (ACTIVE, INACTIVE, FROZEN).
        owner: Reference to the User object who owns this account.
        sim: Reference to the BankingSimulation for recording transactions.
        
    Example:
        >>> account = Account(account_data, user, simulation)
        >>> account.post_transaction(-50.00, "Coffee Shop", "Food", "NYC", "2024-01-15")
    """
    
    def __init__(
        self, 
        data: Dict[str, Any], 
        user: User, 
        simulation: 'BankingSimulation'
    ) -> None:
        """
        Initialize an Account from a dictionary.
        
        Args:
            data: Dictionary containing account attributes.
                  Required keys: account_id, user_id, type, currency,
                  balance, salary_amount, status.
            user: The User object who owns this account.
            simulation: The BankingSimulation instance for transaction recording.
        """
        self.account_id: str = data['account_id']
        self.user_id: str = data['user_id']
        self.type: str = data['type']
        self.currency: str = data['currency']
        self.balance: float = data['balance']
        self.salary_amount: int = data['salary_amount']
        self.status: str = data['status']
        self.owner: User = user
        self.sim: 'BankingSimulation' = simulation

    def post_transaction(
        self, 
        amount: float, 
        description: str, 
        category: str, 
        location: str, 
        date: str, 
        type_override: Optional[str] = None, 
        group_id: Optional[str] = None
    ) -> None:
        """
        Post a transaction to this account.
        
        Updates the account balance and records the transaction in the ledger.
        
        Args:
            amount: Transaction amount (negative for debits, positive for credits).
            description: Human-readable transaction description.
            category: Transaction category (e.g., "Food & Dining", "Income").
            location: Where the transaction occurred.
            date: ISO format date string.
            type_override: Force transaction type instead of inferring from amount.
            group_id: Optional group ID for linking related transactions (e.g., transfers).
            
        Example:
            >>> # Debit transaction
            >>> account.post_transaction(-25.00, "Grocery Store", "Food", "NYC", "2024-01-15")
            >>> # Credit transaction with group ID (transfer)
            >>> account.post_transaction(100.00, "Transfer from acc_123", "Transfer", 
            ...                          "Online", "2024-01-15", group_id="grp_456")
        """
        self.balance += amount
        self.sim.record_account_txn(
            self.account_id, 
            amount, 
            description, 
            category, 
            location, 
            date, 
            type_override, 
            group_id
        )
    
    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"Account(id={self.account_id}, balance={self.balance:.2f})"


class Card(BaseModel):
    """
    Represents a credit card in the simulation.
    
    A Card is linked to an Account and has its own spending limit,
    billing cycle, and spending profile for simulation purposes.
    
    Attributes:
        card_id: Unique identifier (format: "card_{timestamp}_{counter}").
        account_id: ID of the linked account.
        masked_number: Masked card number (e.g., "****-****-****-1234").
        status: Card status (ACTIVE, BLOCKED, EXPIRED).
        limit: Credit limit for the card.
        billing_day: Day of month when bill is due.
        spending_profile: Behavior profile (FRUGAL, AVERAGE, SPENDER).
        current_spend: Current billing cycle spending.
        issue_date: ISO format date when card was issued.
        expiry_date: ISO format date when card expires.
        last_bill_date: ISO format date of last bill payment.
        linked_account: Reference to the Account object.
        sim: Reference to the BankingSimulation for recording transactions.
        
    Example:
        >>> card = Card(card_data, account, simulation)
        >>> result = card.charge(50.00, "Restaurant", "Food", "NYC", "2024-01-15")
        >>> if result is None:
        ...     print("Transaction declined - limit exceeded")
    """
    
    def __init__(
        self, 
        data: Dict[str, Any], 
        account: Account, 
        simulation: 'BankingSimulation'
    ) -> None:
        """
        Initialize a Card from a dictionary.
        
        Args:
            data: Dictionary containing card attributes.
            account: The Account object this card is linked to.
            simulation: The BankingSimulation instance for transaction recording.
        """
        self.card_id: str = data['card_id']
        self.account_id: str = data['account_id']
        self.masked_number: str = data['masked_number']
        self.status: str = data['status']
        self.limit: float = data['limit']
        self.billing_day: int = data['billing_day']
        self.spending_profile: str = data['spending_profile']
        self.current_spend: float = data['current_spend']
        self.issue_date: str = data['issue_date']
        self.expiry_date: str = data['expiry_date']
        self.last_bill_date: Optional[str] = data['last_bill_date']
        self.linked_account: Account = account
        self.sim: 'BankingSimulation' = simulation

    def charge(
        self, 
        amount: float, 
        description: str, 
        category: str, 
        location: str, 
        date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to charge an amount to this card.
        
        Checks if the charge would exceed the credit limit before processing.
        If approved, updates current_spend and records the transaction.
        
        Args:
            amount: Amount to charge (should be positive, will be stored as negative).
            description: Merchant or transaction description.
            category: Transaction category.
            location: Transaction location.
            date: ISO format date string.
            
        Returns:
            Transaction record dict if approved, None if declined (limit exceeded).
            
        Example:
            >>> result = card.charge(100.00, "Electronics Store", "Shopping", "NYC", "2024-01-15")
            >>> if result:
            ...     print(f"Approved: {result['transaction_id']}")
            ... else:
            ...     print("Declined: Credit limit exceeded")
        """
        if self.current_spend + abs(amount) > self.limit:
            return None
        
        self.current_spend += abs(amount)
        return self.sim.record_card_txn(
            self.card_id, 
            amount, 
            description, 
            category, 
            location, 
            date
        )

    def pay_bill(self, date: str) -> None:
        """
        Pay the current billing cycle balance.
        
        Transfers the current_spend amount from the linked account
        and resets the card's current_spend to zero.
        
        Args:
            date: ISO format date string for the payment transaction.
            
        Note:
            Does nothing if current_spend is zero or negative.
        """
        if self.current_spend <= 0:
            return
        
        bill_amount = round(self.current_spend, 2)
        self.linked_account.post_transaction(
            -bill_amount, 
            f"Credit Card Bill (Cycle {self.billing_day})", 
            "Bills", 
            "Online Payment", 
            date, 
            type_override="DEBIT"
        )
        self.current_spend = 0.0
        self.last_bill_date = date
    
    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"Card(id={self.card_id}, spend={self.current_spend:.2f}/{self.limit:.2f})"
