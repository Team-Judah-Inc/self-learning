from abc import ABC, abstractmethod
from flask import current_app
from sqlalchemy import create_engine, text
import os
import json

class BankRepository(ABC):
    """
    Abstract Base Class for Data Access.
    Defines the contract for fetching banking data.
    """
    
    @abstractmethod
    def get_user_by_id(self, user_id): pass

    @abstractmethod
    def get_user_by_username(self, username): pass

    @abstractmethod
    def get_account_by_id(self, account_id): pass

    @abstractmethod
    def get_accounts_by_user(self, user_id): pass

    @abstractmethod
    def get_accounts_by_user_filtered(self, user_id, type=None, currency=None, limit=20, offset=0): pass

    @abstractmethod
    def get_card_by_id(self, card_id): pass

    @abstractmethod
    def get_cards_by_account(self, account_id): pass

    @abstractmethod
    def get_transactions_by_account(self, account_id): pass

    @abstractmethod
    def get_transactions_by_account_filtered(self, account_id, category=None, search=None, sort='desc', limit=20, offset=0): pass

    @abstractmethod
    def get_transactions_by_card(self, card_id): pass

    @abstractmethod
    def get_transactions_by_card_filtered(self, card_id, start_date=None, end_date=None, min_amount=None, limit=20, offset=0): pass

    @abstractmethod
    def get_transaction_by_id(self, transaction_id): pass


class SqlBankRepository(BankRepository):
    """
    Implementation for SQL Database (SQLite, PostgreSQL, etc.)
    """
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)

    def _query(self, query, params=None, one=False):
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]
                if one:
                    return rows[0] if rows else None
                return rows
            except Exception as e:
                print(f"SQL Error: {e}")
                return [] if not one else None

    def get_user_by_id(self, user_id):
        return self._query("SELECT * FROM users WHERE user_id = :uid", {"uid": user_id}, one=True)

    def get_user_by_username(self, username):
        return self._query("SELECT * FROM users WHERE username = :uname", {"uname": username}, one=True)

    def get_account_by_id(self, account_id):
        return self._query("SELECT * FROM accounts WHERE account_id = :aid", {"aid": account_id}, one=True)

    def get_accounts_by_user(self, user_id):
        return self._query("SELECT * FROM accounts WHERE user_id = :uid", {"uid": user_id})

    def get_accounts_by_user_filtered(self, user_id, type=None, currency=None, limit=20, offset=0):
        query = "SELECT * FROM accounts WHERE user_id = :uid"
        params = {"uid": user_id}
        
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

    def get_card_by_id(self, card_id):
        return self._query("SELECT * FROM cards WHERE card_id = :cid", {"cid": card_id}, one=True)

    def get_cards_by_account(self, account_id):
        return self._query("SELECT * FROM cards WHERE account_id = :aid", {"aid": account_id})

    def get_transactions_by_account(self, account_id):
        return self._query("SELECT * FROM account_transactions WHERE account_id = :aid ORDER BY date DESC", {"aid": account_id})

    def get_transactions_by_account_filtered(self, account_id, category=None, search=None, sort='desc', limit=20, offset=0):
        query = "SELECT * FROM account_transactions WHERE account_id = :aid"
        params = {"aid": account_id}
        
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

    def get_transactions_by_card(self, card_id):
        return self._query("SELECT * FROM card_transactions WHERE card_id = :cid ORDER BY date DESC", {"cid": card_id})

    def get_transactions_by_card_filtered(self, card_id, start_date=None, end_date=None, min_amount=None, limit=20, offset=0):
        query = "SELECT * FROM card_transactions WHERE card_id = :cid"
        params = {"cid": card_id}
        
        if start_date:
            query += " AND date >= :start"
            params['start'] = start_date
            
        if end_date:
            query += " AND date <= :end"
            params['end'] = end_date
            
        if min_amount:
            query += " AND ABS(amount) >= :min_amt"
            params['min_amt'] = min_amount
            
        query += " ORDER BY date DESC LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        return self._query(query, params)

    def get_transaction_by_id(self, transaction_id):
        # Try account transactions first
        txn = self._query("SELECT * FROM account_transactions WHERE transaction_id = :tid", {"tid": transaction_id}, one=True)
        if txn: return txn
        # Then card transactions
        return self._query("SELECT * FROM card_transactions WHERE transaction_id = :tid", {"tid": transaction_id}, one=True)


class JsonBankRepository(BankRepository):
    """
    Implementation for JSON Files (Legacy/Fallback)
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def _load_table(self, name):
        path = os.path.join(self.data_dir, f"{name}.json")
        if not os.path.exists(path): return []
        with open(path, 'r') as f:
            try: return json.load(f)
            except: return []

    def get_user_by_id(self, user_id):
        users = self._load_table('users')
        return next((u for u in users if u['user_id'] == user_id), None)

    def get_user_by_username(self, username):
        users = self._load_table('users')
        return next((u for u in users if u['username'] == username), None)

    def get_account_by_id(self, account_id):
        accounts = self._load_table('accounts')
        return next((a for a in accounts if a['account_id'] == account_id), None)

    def get_accounts_by_user(self, user_id):
        accounts = self._load_table('accounts')
        return [a for a in accounts if a['user_id'] == user_id]

    def get_card_by_id(self, card_id):
        cards = self._load_table('cards')
        return next((c for c in cards if c['card_id'] == card_id), None)

    def get_cards_by_account(self, account_id):
        cards = self._load_table('cards')
        return [c for c in cards if c['account_id'] == account_id]

    def get_transactions_by_account(self, account_id):
        txns = self._load_table('account_transactions')
        filtered = [t for t in txns if t['account_id'] == account_id]
        filtered.sort(key=lambda x: x['date'], reverse=True)
        return filtered

    def get_transactions_by_account_filtered(self, account_id, category=None, search=None, sort='desc', limit=20, offset=0):
        # Fallback: Load all and filter in memory
        txns = self.get_transactions_by_account(account_id)
        
        if category:
            txns = [t for t in txns if t.get('category') == category]
            
        if search:
            txns = [t for t in txns if search.lower() in t['description'].lower()]
            
        reverse = (sort == 'desc')
        txns.sort(key=lambda x: x['date'], reverse=reverse)
        
        return txns[offset : offset + limit]

    def get_transactions_by_card(self, card_id):
        txns = self._load_table('card_transactions')
        filtered = [t for t in txns if t.get('card_id') == card_id]
        filtered.sort(key=lambda x: x['date'], reverse=True)
        return filtered

    def get_transactions_by_card_filtered(self, card_id, start_date=None, end_date=None, min_amount=None, limit=20, offset=0):
        # Fallback: Load all and filter in memory
        txns = self.get_transactions_by_card(card_id)
        
        if start_date:
            txns = [t for t in txns if t['date'] >= start_date]
        if end_date:
            txns = [t for t in txns if t['date'] <= end_date]
        if min_amount:
            txns = [t for t in txns if abs(t['amount']) >= min_amount]
            
        return txns[offset : offset + limit]

    def get_transaction_by_id(self, transaction_id):
        txns = self._load_table('account_transactions')
        txn = next((t for t in txns if t['transaction_id'] == transaction_id), None)
        if txn: return txn
        
        txns = self._load_table('card_transactions')
        return next((t for t in txns if t['transaction_id'] == transaction_id), None)


# Singleton Factory
_repo_instance = None

def get_repository() -> BankRepository:
    global _repo_instance
    if _repo_instance:
        return _repo_instance
    
    db_type = current_app.config.get('DB_TYPE', 'json')
    
    if db_type == 'sqlite' or 'sql' in db_type:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        _repo_instance = SqlBankRepository(db_uri)
    else:
        data_dir = current_app.config.get('DATA_DIR', 'mock_data')
        _repo_instance = JsonBankRepository(data_dir)
        
    return _repo_instance