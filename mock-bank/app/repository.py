"""
API Repository Module.

This module provides the data access layer for the Flask API,
supporting both JSON file storage and SQL database backends.

Classes:
    BankRepository: Abstract base class defining the repository interface.
    SqlBankRepository: Implementation for SQL database storage.
    JsonBankRepository: Implementation for JSON file-based storage.

Functions:
    get_repository: Factory function to get the singleton repository instance.
"""

import os
import json
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator

from flask import current_app
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class BankRepository(ABC):
    """
    Abstract Base Class for API Data Access.
    
    Defines the contract for fetching banking data in the API layer.
    All repository implementations must implement these methods.
    """
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their unique identifier.
        
        Args:
            user_id: The user's unique identifier.
            
        Returns:
            User dictionary if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their username.
        
        Args:
            username: The user's login username.
            
        Returns:
            User dictionary if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an account by its unique identifier.
        
        Args:
            account_id: The account's unique identifier.
            
        Returns:
            Account dictionary if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all accounts belonging to a user.
        
        Args:
            user_id: The user's unique identifier.
            
        Returns:
            List of account dictionaries.
        """
        pass

    @abstractmethod
    def get_accounts_by_user_filtered(
        self, 
        user_id: str, 
        type: Optional[str] = None, 
        currency: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get filtered accounts for a user with pagination.
        
        Args:
            user_id: The user's unique identifier.
            type: Optional account type filter.
            currency: Optional currency filter.
            limit: Maximum number of results.
            offset: Number of results to skip.
            
        Returns:
            List of filtered account dictionaries.
        """
        pass

    @abstractmethod
    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a card by its unique identifier.
        
        Args:
            card_id: The card's unique identifier.
            
        Returns:
            Card dictionary if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_cards_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get all cards linked to an account.
        
        Args:
            account_id: The account's unique identifier.
            
        Returns:
            List of card dictionaries.
        """
        pass

    @abstractmethod
    def get_transactions_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get all transactions for an account.
        
        Args:
            account_id: The account's unique identifier.
            
        Returns:
            List of transaction dictionaries, sorted by date descending.
        """
        pass

    @abstractmethod
    def get_transactions_by_account_filtered(
        self, 
        account_id: str, 
        category: Optional[str] = None, 
        search: Optional[str] = None, 
        sort: str = 'desc', 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get filtered transactions for an account with pagination.
        
        Args:
            account_id: The account's unique identifier.
            category: Optional category filter.
            search: Optional search term for descriptions.
            sort: Sort order ('asc' or 'desc').
            limit: Maximum number of results.
            offset: Number of results to skip.
            
        Returns:
            List of filtered transaction dictionaries.
        """
        pass

    @abstractmethod
    def get_transactions_by_card(self, card_id: str) -> List[Dict[str, Any]]:
        """
        Get all transactions for a card.
        
        Args:
            card_id: The card's unique identifier.
            
        Returns:
            List of transaction dictionaries, sorted by date descending.
        """
        pass

    @abstractmethod
    def get_transactions_by_card_filtered(
        self, 
        card_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        min_amount: Optional[float] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get filtered transactions for a card with pagination.
        
        Args:
            card_id: The card's unique identifier.
            start_date: Optional start date filter (ISO format).
            end_date: Optional end date filter (ISO format).
            min_amount: Optional minimum absolute amount filter.
            limit: Maximum number of results.
            offset: Number of results to skip.
            
        Returns:
            List of filtered transaction dictionaries.
        """
        pass

    @abstractmethod
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a transaction by its unique identifier.
        
        Searches both account and card transactions.
        
        Args:
            transaction_id: The transaction's unique identifier.
            
        Returns:
            Transaction dictionary if found, None otherwise.
        """
        pass


# =============================================================================
# SQL Repository Implementation
# =============================================================================

class SqlBankRepository(BankRepository):
    """
    SQL Database Repository Implementation.
    
    Uses SQLAlchemy for database connectivity, supporting SQLite,
    PostgreSQL, and other SQL databases.
    
    Attributes:
        engine: SQLAlchemy engine instance.
    """
    
    def __init__(self, db_uri: str) -> None:
        """
        Initialize the SQL repository.
        
        Args:
            db_uri: SQLAlchemy database URL.
        """
        self.engine: Engine = create_engine(db_uri)

    def _query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None, 
        one: bool = False
    ) -> Any:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string with named parameters.
            params: Dictionary of parameter values.
            one: If True, return only the first result.
            
        Returns:
            List of result dictionaries, or single dict if one=True.
        """
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]
                
                if one:
                    return rows[0] if rows else None
                return rows
            except Exception as e:
                print(f"SQL Error: {e}")
                return None if one else []

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self._query(
            "SELECT * FROM users WHERE user_id = :uid", 
            {"uid": user_id}, 
            one=True
        )

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self._query(
            "SELECT * FROM users WHERE username = :uname", 
            {"uname": username}, 
            one=True
        )

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        return self._query(
            "SELECT * FROM accounts WHERE account_id = :aid", 
            {"aid": account_id}, 
            one=True
        )

    def get_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a user."""
        return self._query(
            "SELECT * FROM accounts WHERE user_id = :uid", 
            {"uid": user_id}
        )

    def get_accounts_by_user_filtered(
        self, 
        user_id: str, 
        type: Optional[str] = None, 
        currency: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered accounts for a user."""
        query = "SELECT * FROM accounts WHERE user_id = :uid"
        params: Dict[str, Any] = {"uid": user_id}
        
        if type:
            query += " AND type = :type"
            params['type'] = type
            
        if currency:
            query += " AND currency = :curr"
            params['curr'] = currency
            
        query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        return self._query(query, params)

    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get card by ID."""
        return self._query(
            "SELECT * FROM cards WHERE card_id = :cid", 
            {"cid": card_id}, 
            one=True
        )

    def get_cards_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all cards for an account."""
        return self._query(
            "SELECT * FROM cards WHERE account_id = :aid", 
            {"aid": account_id}
        )

    def get_transactions_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for an account."""
        return self._query(
            "SELECT * FROM account_transactions WHERE account_id = :aid ORDER BY date DESC", 
            {"aid": account_id}
        )

    def get_transactions_by_account_filtered(
        self, 
        account_id: str, 
        category: Optional[str] = None, 
        search: Optional[str] = None, 
        sort: str = 'desc', 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered transactions for an account."""
        query = "SELECT * FROM account_transactions WHERE account_id = :aid"
        params: Dict[str, Any] = {"aid": account_id}
        
        if category:
            query += " AND category = :cat"
            params['cat'] = category
            
        if search:
            query += " AND description LIKE :search"
            params['search'] = f"%{search}%"
            
        order = "DESC" if sort == 'desc' else "ASC"
        query += f" ORDER BY date {order} LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        return self._query(query, params)

    def get_transactions_by_card(self, card_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a card."""
        return self._query(
            "SELECT * FROM card_transactions WHERE card_id = :cid ORDER BY date DESC", 
            {"cid": card_id}
        )

    def get_transactions_by_card_filtered(
        self, 
        card_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        min_amount: Optional[float] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered transactions for a card."""
        query = "SELECT * FROM card_transactions WHERE card_id = :cid"
        params: Dict[str, Any] = {"cid": card_id}
        
        if start_date:
            query += " AND date >= :start"
            params['start'] = start_date
            
        if end_date:
            query += " AND date <= :end"
            params['end'] = end_date
            
        if min_amount is not None:
            query += " AND ABS(amount) >= :min_amt"
            params['min_amt'] = min_amount
            
        query += " ORDER BY date DESC LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        return self._query(query, params)

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by ID (searches both account and card transactions)."""
        # Try account transactions first
        txn = self._query(
            "SELECT * FROM account_transactions WHERE transaction_id = :tid", 
            {"tid": transaction_id}, 
            one=True
        )
        if txn:
            return txn
        
        # Then try card transactions
        return self._query(
            "SELECT * FROM card_transactions WHERE transaction_id = :tid", 
            {"tid": transaction_id}, 
            one=True
        )


# =============================================================================
# JSON Repository Implementation
# =============================================================================

class JsonBankRepository(BankRepository):
    """
    JSON File-based Repository Implementation.
    
    Stores data in flat JSON files. Suitable for development and testing.
    
    Attributes:
        data_dir: Directory path for JSON files.
    """
    
    def __init__(self, data_dir: str) -> None:
        """
        Initialize the JSON repository.
        
        Args:
            data_dir: Directory path for JSON files.
        """
        self.data_dir = data_dir

    def _load_table(self, name: str) -> List[Dict[str, Any]]:
        """
        Load data from a JSON file.
        
        Args:
            name: Table name (without .json extension).
            
        Returns:
            List of records, or empty list if file doesn't exist.
        """
        path = os.path.join(self.data_dir, f"{name}.json")
        
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        users = self._load_table('users')
        return next((u for u in users if u['user_id'] == user_id), None)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        users = self._load_table('users')
        return next((u for u in users if u['username'] == username), None)

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        accounts = self._load_table('accounts')
        return next((a for a in accounts if a['account_id'] == account_id), None)

    def get_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a user."""
        accounts = self._load_table('accounts')
        return [a for a in accounts if a['user_id'] == user_id]

    def get_accounts_by_user_filtered(
        self, 
        user_id: str, 
        type: Optional[str] = None, 
        currency: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered accounts for a user."""
        accounts = self.get_accounts_by_user(user_id)
        
        if type:
            accounts = [a for a in accounts if a.get('type') == type]
            
        if currency:
            accounts = [a for a in accounts if a.get('currency') == currency]
            
        return accounts[offset:offset + limit]

    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get card by ID."""
        cards = self._load_table('cards')
        return next((c for c in cards if c['card_id'] == card_id), None)

    def get_cards_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all cards for an account."""
        cards = self._load_table('cards')
        return [c for c in cards if c['account_id'] == account_id]

    def get_transactions_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for an account."""
        txns = self._load_table('account_transactions')
        filtered = [t for t in txns if t['account_id'] == account_id]
        filtered.sort(key=lambda x: x['date'], reverse=True)
        return filtered

    def get_transactions_by_account_filtered(
        self, 
        account_id: str, 
        category: Optional[str] = None, 
        search: Optional[str] = None, 
        sort: str = 'desc', 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered transactions for an account."""
        txns = self.get_transactions_by_account(account_id)
        
        if category:
            txns = [t for t in txns if t.get('category') == category]
            
        if search:
            search_lower = search.lower()
            txns = [t for t in txns if search_lower in t['description'].lower()]
            
        reverse = (sort == 'desc')
        txns.sort(key=lambda x: x['date'], reverse=reverse)
        
        return txns[offset:offset + limit]

    def get_transactions_by_card(self, card_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a card."""
        txns = self._load_table('card_transactions')
        filtered = [t for t in txns if t.get('card_id') == card_id]
        filtered.sort(key=lambda x: x['date'], reverse=True)
        return filtered

    def get_transactions_by_card_filtered(
        self, 
        card_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        min_amount: Optional[float] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get filtered transactions for a card."""
        txns = self.get_transactions_by_card(card_id)
        
        if start_date:
            txns = [t for t in txns if t['date'] >= start_date]
        
        if end_date:
            txns = [t for t in txns if t['date'] <= end_date]
        
        if min_amount is not None:
            txns = [t for t in txns if abs(t['amount']) >= min_amount]
            
        return txns[offset:offset + limit]

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by ID (searches both account and card transactions)."""
        # Try account transactions first
        txns = self._load_table('account_transactions')
        txn = next((t for t in txns if t['transaction_id'] == transaction_id), None)
        if txn:
            return txn
        
        # Then try card transactions
        txns = self._load_table('card_transactions')
        return next((t for t in txns if t['transaction_id'] == transaction_id), None)


# =============================================================================
# Repository Factory
# =============================================================================

# Singleton instance
_repo_instance: Optional[BankRepository] = None


def get_repository() -> BankRepository:
    """
    Get the singleton repository instance.
    
    Creates the appropriate repository type based on app configuration
    on first call, then returns the cached instance.
    
    Returns:
        BankRepository instance configured for the current environment.
        
    Note:
        This function must be called within a Flask application context.
    """
    global _repo_instance
    
    if _repo_instance is not None:
        return _repo_instance
    
    db_type = current_app.config.get('DB_TYPE', 'json').lower()
    
    if db_type == 'sqlite' or 'sql' in db_type:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        _repo_instance = SqlBankRepository(db_uri)
    else:
        data_dir = current_app.config.get('DATA_DIR', 'mock_data')
        _repo_instance = JsonBankRepository(data_dir)
        
    return _repo_instance


def reset_repository() -> None:
    """
    Reset the singleton repository instance.
    
    Useful for testing to ensure a fresh repository is created.
    """
    global _repo_instance
    _repo_instance = None
