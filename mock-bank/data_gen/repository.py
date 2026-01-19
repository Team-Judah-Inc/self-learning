import os
import json
import datetime
from abc import ABC, abstractmethod
from typing import Any

# --- FIX: Relative Import ---
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from .config import DEFAULT_CONFIG
from .sql_models import Base, UserSQL, AccountSQL, CardSQL, AccountTransactionSQL, CardTransactionSQL, BankMetadataSQL

class DataRepository(ABC):
    @abstractmethod
    def load_config(self) -> dict: pass
    @abstractmethod
    def load_metadata(self) -> dict: pass
    @abstractmethod
    def load_resources(self): pass
    @abstractmethod
    def save_all(self, users, accounts, cards, acc_txns, card_txns, metadata): pass
    @abstractmethod
    def generate_id(self, entity_type: str, existing_list: list = None) -> str: pass

class JsonRepository(DataRepository):
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._id_counters = {} 
        os.makedirs(data_dir, exist_ok=True)

    def _load_json(self, filename: str, default: Any = None) -> Any:
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
        return default if default is not None else []

    def _save_json(self, filename: str, data: Any):
        with open(os.path.join(self.data_dir, filename), 'w') as f:
            json.dump(data, f, indent=2)

    def load_config(self) -> dict:
        config = self._load_json('bank_configuration.json', DEFAULT_CONFIG)
        if not os.path.exists(os.path.join(self.data_dir, 'bank_configuration.json')):
            self._save_json('bank_configuration.json', config)
        return config

    def load_metadata(self) -> dict:
        return self._load_json('bank_metadata.json', {"current_date": datetime.date.today().isoformat()})

    def load_resources(self):
        return (
            self._load_json('users.json', []),
            self._load_json('accounts.json', []),
            self._load_json('cards.json', []),
            self._load_json('account_transactions.json', []),
            self._load_json('card_transactions.json', [])
        )

    def save_all(self, users, accounts, cards, acc_txns, card_txns, metadata):
        self._save_json('bank_metadata.json', metadata)
        self._save_json('users.json', [self._clean(u) for u in users])
        self._save_json('accounts.json', [self._clean(a) for a in accounts])
        self._save_json('cards.json', [self._clean(c) for c in cards])
        self._save_json('account_transactions.json', acc_txns)
        self._save_json('card_transactions.json', card_txns)

    def _clean(self, obj):
        d = obj.__dict__.copy()
        for k in ['owner', 'linked_account', 'repo', 'sim']: 
            if k in d: del d[k]
        return d

    def generate_id(self, entity_type: str, existing_list: list = None) -> str:
        prefix_map = {'user': ('u', 'user_id'), 'account': ('acc', 'account_id'), 'card': ('card', 'card_id'), 'atxn': ('atxn', 'transaction_id'), 'ctxn': ('ctxn', 'transaction_id')}
        prefix, key = prefix_map[entity_type]
        if not existing_list: 
             val = self._id_counters.get(entity_type, 0) + 1
             self._id_counters[entity_type] = val
             return f"{prefix}_{val}"
        ids = [int(x[key].split('_')[1]) if isinstance(x, dict) else int(getattr(x, key).split('_')[1]) for x in existing_list]
        next_val = max(ids) + 1 if ids else 1
        return f"{prefix}_{next_val}"

class SqlRepository(DataRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._id_counters = {}

    def load_config(self) -> dict:
        # Config is still file-based for now as it's static rules
        # But we could move it to DB if needed. For now, let's keep it simple
        # and maybe just return default if file not found, or use a hybrid approach.
        # Given the prompt, let's stick to the pattern but maybe just use the default config
        # or read from a file if we want to keep that flexibility.
        # However, the interface requires it. Let's just return DEFAULT_CONFIG for now
        # or read from the file system if we want to keep that part file-based.
        # Let's assume config stays as a file for simulation rules.
        return DEFAULT_CONFIG

    def load_metadata(self) -> dict:
        session = self.Session()
        try:
            meta = session.query(BankMetadataSQL).filter_by(key='metadata').first()
            if meta:
                return meta.value
            return {"current_date": datetime.date.today().isoformat()}
        finally:
            session.close()

    def load_resources(self):
        session = self.Session()
        try:
            users = [u.__dict__ for u in session.query(UserSQL).all()]
            accounts = [a.__dict__ for a in session.query(AccountSQL).all()]
            cards = [c.__dict__ for c in session.query(CardSQL).all()]
            acc_txns = [t.__dict__ for t in session.query(AccountTransactionSQL).all()]
            card_txns = [t.__dict__ for t in session.query(CardTransactionSQL).all()]
            
            # Clean up sqlalchemy state
            for l in [users, accounts, cards, acc_txns, card_txns]:
                for item in l:
                    if '_sa_instance_state' in item:
                        del item['_sa_instance_state']
            
            return users, accounts, cards, acc_txns, card_txns
        finally:
            session.close()

    def save_all(self, users, accounts, cards, acc_txns, card_txns, metadata):
        session = self.Session()
        try:
            # This is a naive "save all" that wipes and recreates or upserts.
            # For a simulation that evolves, upsert is better, but "save_all" implies full state dump.
            # Given the current architecture dumps everything to JSON, we can try to mirror that
            # but it's inefficient for SQL.
            # A better approach for SQL is to save incrementally, but to fit the interface:
            
            # 1. Metadata
            meta_entry = session.query(BankMetadataSQL).filter_by(key='metadata').first()
            if not meta_entry:
                meta_entry = BankMetadataSQL(key='metadata', value=metadata)
                session.add(meta_entry)
            else:
                meta_entry.value = metadata

            # 2. Users (Upsert)
            for u in users:
                u_dict = self._clean(u)
                existing = session.query(UserSQL).filter_by(user_id=u.user_id).first()
                if existing:
                    for k, v in u_dict.items(): setattr(existing, k, v)
                else:
                    session.add(UserSQL(**u_dict))

            # 3. Accounts
            for a in accounts:
                a_dict = self._clean(a)
                existing = session.query(AccountSQL).filter_by(account_id=a.account_id).first()
                if existing:
                    for k, v in a_dict.items(): setattr(existing, k, v)
                else:
                    session.add(AccountSQL(**a_dict))

            # 4. Cards
            for c in cards:
                c_dict = self._clean(c)
                existing = session.query(CardSQL).filter_by(card_id=c.card_id).first()
                if existing:
                    for k, v in c_dict.items(): setattr(existing, k, v)
                else:
                    session.add(CardSQL(**c_dict))

            # 5. Transactions (Only add new ones ideally, but let's check existence)
            # Optimization: Only check if we suspect they are new.
            # For now, simple check.
            for t in acc_txns:
                if not session.query(AccountTransactionSQL).filter_by(transaction_id=t['transaction_id']).first():
                    session.add(AccountTransactionSQL(**t))
            
            for t in card_txns:
                if not session.query(CardTransactionSQL).filter_by(transaction_id=t['transaction_id']).first():
                    session.add(CardTransactionSQL(**t))

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _clean(self, obj):
        d = obj.__dict__.copy()
        for k in ['owner', 'linked_account', 'repo', 'sim', '_sa_instance_state']:
            if k in d: del d[k]
        return d

    def generate_id(self, entity_type: str, existing_list: list = None) -> str:
        # We can use the same logic, or query DB for max ID.
        # To keep it compatible with the "existing_list" passed from simulation (which is in-memory),
        # we can stick to the base logic.
        prefix_map = {'user': ('u', 'user_id'), 'account': ('acc', 'account_id'), 'card': ('card', 'card_id'), 'atxn': ('atxn', 'transaction_id'), 'ctxn': ('ctxn', 'transaction_id')}
        prefix, key = prefix_map[entity_type]
        
        if existing_list:
             ids = [int(x[key].split('_')[1]) if isinstance(x, dict) else int(getattr(x, key).split('_')[1]) for x in existing_list]
             next_val = max(ids) + 1 if ids else 1
             return f"{prefix}_{next_val}"
        
        # Fallback if list not provided (shouldn't happen in current sim logic)
        return f"{prefix}_{int(datetime.datetime.now().timestamp())}"