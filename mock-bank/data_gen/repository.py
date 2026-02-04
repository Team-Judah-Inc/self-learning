"""
Data Repository Module for Banking Simulation.

This module provides the data access layer for the banking simulation,
supporting both JSON file storage and SQL database backends.

Classes:
    DataRepository: Abstract base class defining the repository interface.
    JsonRepository: Implementation for JSON file-based storage.
    SqlRepository: Implementation for SQL database storage (SQLite, PostgreSQL).

The repository pattern abstracts data persistence, allowing the simulation
to work with different storage backends without code changes.
"""

import os
import json
import datetime
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, List, Optional, Dict, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import DEFAULT_CONFIG, clean_model_dict
from .sql_models import (
    Base, 
    UserSQL, 
    AccountSQL, 
    CardSQL, 
    AccountTransactionSQL, 
    CardTransactionSQL, 
    BankMetadataSQL
)


class DataRepository(ABC):
    """
    Abstract Base Class for Data Access.
    
    Defines the contract for fetching and saving banking data.
    All repository implementations must implement these methods.
    
    This abstraction allows the simulation to work with different
    storage backends (JSON files, SQLite, PostgreSQL, etc.) without
    changing the business logic.
    """
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """
        Load the simulation configuration.
        
        Returns:
            Configuration dictionary with probabilities, financial settings, etc.
        """
        pass
    
    @abstractmethod
    def load_metadata(self) -> Dict[str, Any]:
        """
        Load simulation metadata (current date, etc.).
        
        Returns:
            Metadata dictionary.
        """
        pass
    
    @abstractmethod
    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Save simulation metadata.
        
        Args:
            metadata: Metadata dictionary to persist.
        """
        pass
    
    @abstractmethod
    def get_accounts_batch(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch a batch of accounts for processing.
        
        Args:
            limit: Maximum number of accounts to return.
            offset: Number of accounts to skip.
            
        Returns:
            List of account dictionaries.
        """
        pass
    
    @abstractmethod
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """
        Fetch all accounts.
        
        Returns:
            List of all account dictionaries.
        """
        pass
    
    @abstractmethod
    def get_cards_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all cards linked to an account.
        
        Args:
            account_id: The account's unique identifier.
            
        Returns:
            List of card dictionaries.
        """
        pass
    
    @abstractmethod
    def get_cards_batch(self, account_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch cards for multiple accounts in a single query.
        
        Args:
            account_ids: List of account IDs to fetch cards for.
            
        Returns:
            Dictionary mapping account_id to list of card dictionaries.
        """
        pass
    
    @abstractmethod
    def get_user_city_map(self, user_ids: List[str]) -> Dict[str, str]:
        """
        Fetch city information for multiple users.
        
        Args:
            user_ids: List of user IDs.
            
        Returns:
            Dictionary mapping user_id to city name.
        """
        pass
    
    @abstractmethod
    def save_transactions(
        self, 
        account_txns: List[Dict[str, Any]], 
        card_txns: List[Dict[str, Any]]
    ) -> None:
        """
        Save new transactions to storage.
        
        Args:
            account_txns: List of account transaction dictionaries.
            card_txns: List of card transaction dictionaries.
        """
        pass
    
    @abstractmethod
    def generate_id(self, entity_type: str, existing_list: Optional[List] = None) -> str:
        """
        Generate a unique identifier for an entity.
        
        Args:
            entity_type: Type of entity ('user', 'account', 'card', 'atxn', 'ctxn').
            existing_list: Optional list of existing entities for ID collision avoidance.
            
        Returns:
            Unique identifier string.
        """
        pass
    
    @abstractmethod
    def load_resources(self) -> tuple:
        """
        Load all resources from storage (legacy method for initialization).
        
        Returns:
            Tuple of (users, accounts, cards, account_txns, card_txns).
        """
        pass
    
    @abstractmethod
    def save_all(
        self, 
        users: List, 
        accounts: List, 
        cards: List, 
        acc_txns: List, 
        card_txns: List, 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save all resources to storage (legacy method for initialization).
        
        Args:
            users: List of user objects.
            accounts: List of account objects.
            cards: List of card objects.
            acc_txns: List of account transaction dictionaries.
            card_txns: List of card transaction dictionaries.
            metadata: Metadata dictionary.
        """
        pass


class JsonRepository(DataRepository):
    """
    JSON File-based Repository Implementation.
    
    Stores data in flat JSON files in a specified directory.
    Suitable for development, testing, and small-scale simulations.
    
    File Structure:
        {data_dir}/
            bank_configuration.json
            bank_metadata.json
            users.json
            accounts.json
            cards.json
            account_transactions.json
            card_transactions.json
            
    Attributes:
        data_dir: Directory path for JSON files.
        
    Note:
        This implementation loads entire files for each operation,
        which is inefficient for large datasets. Use SqlRepository
        for production workloads.
    """
    
    def __init__(self, data_dir: str) -> None:
        """
        Initialize the JSON repository.
        
        Args:
            data_dir: Directory path for storing JSON files.
                      Will be created if it doesn't exist.
        """
        self.data_dir = data_dir
        self._id_counters: Dict[str, int] = {}
        os.makedirs(data_dir, exist_ok=True)

    def _load_json(self, filename: str, default: Any = None) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the JSON file (without path).
            default: Default value if file doesn't exist.
            
        Returns:
            Parsed JSON data or default value.
        """
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default if default is not None else []

    def _save_json(self, filename: str, data: Any) -> None:
        """
        Save data to a JSON file.
        
        Args:
            filename: Name of the JSON file (without path).
            data: Data to serialize and save.
        """
        path = os.path.join(self.data_dir, filename)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration, creating default if not exists."""
        config_path = os.path.join(self.data_dir, 'bank_configuration.json')
        config = self._load_json('bank_configuration.json', DEFAULT_CONFIG)
        
        if not os.path.exists(config_path):
            self._save_json('bank_configuration.json', config)
        
        return config

    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata with default current date."""
        return self._load_json(
            'bank_metadata.json', 
            {"current_date": datetime.date.today().isoformat()}
        )

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to file."""
        self._save_json('bank_metadata.json', metadata)

    def get_accounts_batch(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a batch of accounts.
        
        Note: For JSON, we load all accounts and slice in memory.
        """
        all_accounts = self._load_json('accounts.json', [])
        return all_accounts[offset:offset + limit]
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        return self._load_json('accounts.json', [])

    def get_cards_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all cards for a specific account."""
        cards = self._load_json('cards.json', [])
        return [c for c in cards if c['account_id'] == account_id]
    
    def get_cards_batch(self, account_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get cards for multiple accounts efficiently.
        
        Args:
            account_ids: List of account IDs.
            
        Returns:
            Dictionary mapping account_id to list of cards.
        """
        cards = self._load_json('cards.json', [])
        account_id_set = set(account_ids)
        
        result: Dict[str, List[Dict[str, Any]]] = {aid: [] for aid in account_ids}
        for card in cards:
            if card['account_id'] in account_id_set:
                result[card['account_id']].append(card)
        
        return result

    def get_user_city_map(self, user_ids: List[str]) -> Dict[str, str]:
        """Get city mapping for multiple users."""
        users = self._load_json('users.json', [])
        user_id_set = set(user_ids)
        return {
            u['user_id']: u.get('city', 'Unknown') 
            for u in users 
            if u['user_id'] in user_id_set
        }

    def save_transactions(
        self, 
        account_txns: List[Dict[str, Any]], 
        card_txns: List[Dict[str, Any]]
    ) -> None:
        """
        Append new transactions to existing files.
        
        Note: This loads all existing transactions, appends new ones,
        and saves everything. Inefficient for large datasets.
        """
        existing_acc_txns = self._load_json('account_transactions.json', [])
        existing_card_txns = self._load_json('card_transactions.json', [])
        
        existing_acc_txns.extend(account_txns)
        existing_card_txns.extend(card_txns)
        
        self._save_json('account_transactions.json', existing_acc_txns)
        self._save_json('card_transactions.json', existing_card_txns)

    def load_resources(self) -> tuple:
        """Load all resources for initialization."""
        return (
            self._load_json('users.json', []),
            self._load_json('accounts.json', []),
            self._load_json('cards.json', []),
            self._load_json('account_transactions.json', []),
            self._load_json('card_transactions.json', [])
        )

    def save_all(
        self, 
        users: List, 
        accounts: List, 
        cards: List, 
        acc_txns: List, 
        card_txns: List, 
        metadata: Dict[str, Any]
    ) -> None:
        """Save all resources to files."""
        self._save_json('bank_metadata.json', metadata)
        self._save_json('users.json', [clean_model_dict(u) for u in users])
        self._save_json('accounts.json', [clean_model_dict(a) for a in accounts])
        self._save_json('cards.json', [clean_model_dict(c) for c in cards])
        self._save_json('account_transactions.json', acc_txns)
        self._save_json('card_transactions.json', card_txns)

    def generate_id(self, entity_type: str, existing_list: Optional[List] = None) -> str:
        """
        Generate a unique ID for an entity.
        
        Uses timestamp + counter for uniqueness.
        """
        prefix_map = {
            'user': ('u', 'user_id'), 
            'account': ('acc', 'account_id'), 
            'card': ('card', 'card_id'), 
            'atxn': ('atxn', 'transaction_id'), 
            'ctxn': ('ctxn', 'transaction_id')
        }
        prefix, key = prefix_map[entity_type]
        
        # Increment counter
        val = self._id_counters.get(entity_type, 0) + 1
        self._id_counters[entity_type] = val
        
        # Check existing list for higher IDs (legacy compatibility)
        if existing_list:
            try:
                ids = [
                    int(x[key].split('_')[1]) if isinstance(x, dict) 
                    else int(getattr(x, key).split('_')[1]) 
                    for x in existing_list
                ]
                if ids:
                    next_val = max(ids) + 1
                    if next_val > val:
                        self._id_counters[entity_type] = next_val
                        return f"{prefix}_{next_val}"
            except (ValueError, IndexError, AttributeError):
                pass
        
        timestamp = int(datetime.datetime.now().timestamp())
        return f"{prefix}_{timestamp}_{val}"


class SqlRepository(DataRepository):
    """
    SQL Database Repository Implementation.
    
    Uses SQLAlchemy for ORM mapping, supporting SQLite, PostgreSQL,
    and other SQL databases.
    
    Attributes:
        engine: SQLAlchemy engine instance.
        Session: Session factory for creating database sessions.
        
    Example:
        >>> repo = SqlRepository("sqlite:///bank.db")
        >>> accounts = repo.get_accounts_batch(limit=10)
    """
    
    def __init__(self, db_url: str) -> None:
        """
        Initialize the SQL repository.
        
        Args:
            db_url: SQLAlchemy database URL.
                    Examples:
                    - "sqlite:///bank.db"
                    - "postgresql://user:pass@localhost/bank"
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._id_counters: Dict[str, int] = {}
    
    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Handles session lifecycle, commit, and rollback automatically.
        
        Yields:
            SQLAlchemy Session instance.
            
        Example:
            >>> with self._get_session() as session:
            ...     users = session.query(UserSQL).all()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def _clean_sqlalchemy_dict(self, obj_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove SQLAlchemy internal state from a dictionary.
        
        Args:
            obj_dict: Dictionary from SQLAlchemy model.__dict__.
            
        Returns:
            Cleaned dictionary without _sa_instance_state.
        """
        return {k: v for k, v in obj_dict.items() if k != '_sa_instance_state'}

    def load_config(self) -> Dict[str, Any]:
        """Load default configuration (SQL doesn't store config)."""
        return DEFAULT_CONFIG

    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from database."""
        with self._get_session() as session:
            meta = session.query(BankMetadataSQL).filter_by(key='metadata').first()
            if meta:
                return meta.value
            return {"current_date": datetime.date.today().isoformat()}

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to database."""
        with self._get_session() as session:
            meta_entry = session.query(BankMetadataSQL).filter_by(key='metadata').first()
            if not meta_entry:
                meta_entry = BankMetadataSQL(key='metadata', value=metadata)
                session.add(meta_entry)
            else:
                meta_entry.value = metadata

    def get_accounts_batch(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get a batch of accounts from database."""
        with self._get_session() as session:
            accounts = session.query(AccountSQL).limit(limit).offset(offset).all()
            return [self._clean_sqlalchemy_dict(a.__dict__) for a in accounts]
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts from database."""
        with self._get_session() as session:
            accounts = session.query(AccountSQL).all()
            return [self._clean_sqlalchemy_dict(a.__dict__) for a in accounts]

    def get_cards_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get all cards for a specific account."""
        with self._get_session() as session:
            cards = session.query(CardSQL).filter_by(account_id=account_id).all()
            return [self._clean_sqlalchemy_dict(c.__dict__) for c in cards]
    
    def get_cards_batch(self, account_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get cards for multiple accounts in a single query.
        
        Optimized to avoid N+1 query problem.
        """
        with self._get_session() as session:
            cards = session.query(CardSQL).filter(
                CardSQL.account_id.in_(account_ids)
            ).all()
            
            result: Dict[str, List[Dict[str, Any]]] = {aid: [] for aid in account_ids}
            for card in cards:
                card_dict = self._clean_sqlalchemy_dict(card.__dict__)
                result[card.account_id].append(card_dict)
            
            return result

    def get_user_city_map(self, user_ids: List[str]) -> Dict[str, str]:
        """Get city mapping for multiple users."""
        with self._get_session() as session:
            users = session.query(
                UserSQL.user_id, 
                UserSQL.city
            ).filter(UserSQL.user_id.in_(user_ids)).all()
            return {u.user_id: u.city for u in users}

    def save_transactions(
        self, 
        account_txns: List[Dict[str, Any]], 
        card_txns: List[Dict[str, Any]]
    ) -> None:
        """Save new transactions to database."""
        with self._get_session() as session:
            for txn in account_txns:
                session.add(AccountTransactionSQL(**txn))
            for txn in card_txns:
                session.add(CardTransactionSQL(**txn))

    def load_resources(self) -> tuple:
        """Load all resources for initialization."""
        with self._get_session() as session:
            users = [self._clean_sqlalchemy_dict(u.__dict__) 
                     for u in session.query(UserSQL).all()]
            accounts = [self._clean_sqlalchemy_dict(a.__dict__) 
                        for a in session.query(AccountSQL).all()]
            cards = [self._clean_sqlalchemy_dict(c.__dict__) 
                     for c in session.query(CardSQL).all()]
            acc_txns = [self._clean_sqlalchemy_dict(t.__dict__) 
                        for t in session.query(AccountTransactionSQL).all()]
            card_txns = [self._clean_sqlalchemy_dict(t.__dict__) 
                         for t in session.query(CardTransactionSQL).all()]
            
            return users, accounts, cards, acc_txns, card_txns

    def save_all(
        self, 
        users: List, 
        accounts: List, 
        cards: List, 
        acc_txns: List, 
        card_txns: List, 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save all resources to database (upsert pattern).
        
        Used primarily for initialization and full state saves.
        """
        self.save_metadata(metadata)
        
        with self._get_session() as session:
            # Upsert users
            for u in users:
                u_dict = clean_model_dict(u)
                existing = session.query(UserSQL).filter_by(user_id=u.user_id).first()
                if existing:
                    for k, v in u_dict.items():
                        setattr(existing, k, v)
                else:
                    session.add(UserSQL(**u_dict))

            # Upsert accounts
            for a in accounts:
                a_dict = clean_model_dict(a)
                existing = session.query(AccountSQL).filter_by(account_id=a.account_id).first()
                if existing:
                    for k, v in a_dict.items():
                        setattr(existing, k, v)
                else:
                    session.add(AccountSQL(**a_dict))

            # Upsert cards
            for c in cards:
                c_dict = clean_model_dict(c)
                existing = session.query(CardSQL).filter_by(card_id=c.card_id).first()
                if existing:
                    for k, v in c_dict.items():
                        setattr(existing, k, v)
                else:
                    session.add(CardSQL(**c_dict))

    def generate_id(self, entity_type: str, existing_list: Optional[List] = None) -> str:
        """
        Generate a unique ID using timestamp and counter.
        
        Thread-safe for single-process usage.
        """
        prefix_map = {
            'user': ('u', 'user_id'), 
            'account': ('acc', 'account_id'), 
            'card': ('card', 'card_id'), 
            'atxn': ('atxn', 'transaction_id'), 
            'ctxn': ('ctxn', 'transaction_id')
        }
        prefix, _ = prefix_map[entity_type]
        
        val = self._id_counters.get(entity_type, 0) + 1
        self._id_counters[entity_type] = val
        
        timestamp = int(datetime.datetime.now().timestamp())
        return f"{prefix}_{timestamp}_{val}"
