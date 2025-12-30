import os
import json
import datetime
from abc import ABC, abstractmethod
from typing import Any

# --- FIX: Relative Import ---
from .config import DEFAULT_CONFIG

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