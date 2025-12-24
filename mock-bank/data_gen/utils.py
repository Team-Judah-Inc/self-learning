import json
import os
import datetime
import random
from faker import Faker
from .config import DATA_DIR, DEFAULT_CONFIG

fake = Faker()

# ==========================================
# --- FILE I/O HELPERS ---
# ==========================================

def load_json(filename, default=None):
    """Safely loads a JSON file from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else []
    return default if default is not None else []

def save_json(filename, data):
    """Writes data to a JSON file with indentation for readability."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    """
    Initializes the simulation state.
    Loads or creates configuration, metadata, and resource files.
    """
    # 1. Load or Create Configuration
    config_path = os.path.join(DATA_DIR, 'bank_configuration.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        print("Configuration not found. Creating default 'bank_configuration.json'...")
        config = DEFAULT_CONFIG
        save_json('bank_configuration.json', config)

    # 2. Load Metadata
    metadata = load_json('bank_metadata.json', {
        "current_date": datetime.date.today().isoformat()
    })

    return {
        'configuration': config,
        'metadata': metadata,
        'users': load_json('users.json', []),
        'accounts': load_json('accounts.json', []),
        'cards': load_json('cards.json', []),
        'transactions': load_json('transactions.json', [])
    }

def save_data(data):
    """Persists the current state (metadata and resources) to JSON files."""
    save_json('bank_metadata.json', data['metadata'])
    save_json('users.json', data['users'])
    save_json('accounts.json', data['accounts'])
    save_json('cards.json', data['cards'])
    save_json('transactions.json', data['transactions'])

# ==========================================
# --- LOGIC HELPERS ---
# ==========================================

def get_next_id(list_data, prefix):
    """Calculates the next incremental ID (e.g., 'u_5' -> 6)."""
    if not list_data:
        return 1
    valid_ids = []
    id_key = f'{prefix}_id'
    for item in list_data:
        try:
            # Extracts '5' from 'u_5' or 'acc_5'
            valid_ids.append(int(item[id_key].split('_')[1]))
        except (IndexError, ValueError):
            continue
    return max(valid_ids) + 1 if valid_ids else 1

def get_consistent_company(user_id):
    """Generates a stable company name based on the User ID seed."""
    try:
        seed_val = int(user_id.split('_')[1])
    except (IndexError, ValueError):
        seed_val = hash(user_id)
    
    temp_fake = Faker()
    temp_fake.seed_instance(seed_val)
    return f"{temp_fake.company()} {temp_fake.company_suffix()}"

def pick_weighted_category(config):
    """Selects a transaction category based on configuration probabilities."""
    cats_dict = config['probabilities']['categories']
    cats = list(cats_dict.keys())
    weights = list(cats_dict.values())
    return random.choices(cats, weights=weights, k=1)[0]

def pick_location(home_city, config):
    """Determines if a transaction happens in the home city or elsewhere."""
    chance = config['probabilities']['home_location_chance']
    if random.random() < chance:
        return home_city
    return fake.city()

# ==========================================
# --- REPORTING HELPERS ---
# ==========================================

def read_balances(data, user_id=None):
    """Prints a formatted balance sheet to the console."""
    header = f"{'USER ID':<10} | {'ACCOUNT ID':<12} | {'TYPE':<10} | {'BALANCE ($)':>12}"
    print(header)
    print("-" * len(header))
    for acc in data['accounts']:
        if user_id and acc['user_id'] != user_id:
            continue
        print(f"{acc['user_id']:<10} | {acc['account_id']:<12} | {acc['type']:<10} | {acc['balance']:>12.2f}")
    print("-" * len(header))
    print(f"System Date: {data['metadata']['current_date']}")