import json
import random
import os
import argparse
import datetime
import textwrap
from faker import Faker
from werkzeug.security import generate_password_hash

fake = Faker()
Faker.seed(12345)
DATA_DIR = 'mock_data'
os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# --- ⚙️ DEFAULT CONFIGURATION ---
# ==========================================
# This dictionary serves as the fallback schema.
# On the first run, this is written to 'bank_configuration.json'.
DEFAULT_CONFIG = {
    "probabilities": {
        "home_location_chance": 0.90,
        "categories": {
            "Food & Dining": 0.30,
            "Shopping": 0.20,
            "Transport": 0.15,
            "Entertainment": 0.10,
            "Health & Wellness": 0.10,
            "Travel": 0.05,
            "Utilities": 0.10
        }
    },
    "financial": {
        "initial_balance_range": [1000, 5000],
        "salary_range": [3000, 9000],
        "default_credit_limit": 5000,
        "manual_transaction_default": -10.00,
        "transfer_default_amount": 50.00
    },
    "time": {
        "payroll_days": [1, 15],
        "billing_cycle_options": [1, 10, 15],
        "card_expiry_years": 3
    },
    "behavior": {
        "spending_profiles": {
            "FRUGAL":  {"prob": 0.1, "mean": 15.00,  "std": 5.00,  "min": 2.00,  "max": 60.00},
            "AVERAGE": {"prob": 0.4, "mean": 45.00,  "std": 20.00, "min": 5.00,  "max": 200.00},
            "SPENDER": {"prob": 0.7, "mean": 120.00, "std": 80.00, "min": 10.00, "max": 800.00}
        }
    }
}

# ==========================================
# --- HELPERS ---
# ==========================================

def get_consistent_company(user_id):
    """
    Generates a consistent employer name based on the User ID.
    This ensures 'user_1' always works for the same company across runs.
    
    Args:
        user_id (str): The user ID (e.g., 'u_1').
        
    Returns:
        str: A fake company name.
    """
    try: seed_val = int(user_id.split('_')[1])
    except: seed_val = hash(user_id)
    temp_fake = Faker()
    temp_fake.seed_instance(seed_val)
    return f"{temp_fake.company()} {temp_fake.company_suffix()}"

def get_next_id(list_data, prefix):
    """
    Calculates the next incremental ID for a resource list.
    
    Args:
        list_data (list): The list of existing dictionaries (users, cards, etc.).
        prefix (str): The prefix to parse (e.g., 'user' for 'user_id').
        
    Returns:
        int: The next available integer ID.
    """
    if not list_data: return 1
    valid_ids = []
    for x in list_data:
        try: valid_ids.append(int(x[f'{prefix}_id'].split('_')[1]))
        except: continue
    return max(valid_ids) + 1 if valid_ids else 1

def pick_weighted_category(config):
    """
    Selects a transaction category based on weighted probabilities defined in config.
    
    Args:
        config (dict): The loaded bank_configuration.json.
        
    Returns:
        str: A category name (e.g., "Food & Dining").
    """
    cats_dict = config['probabilities']['categories']
    cats = list(cats_dict.keys())
    weights = list(cats_dict.values())
    return random.choices(cats, weights=weights, k=1)[0]

def pick_location(home_city, config):
    """
    Determines if a transaction happens in the user's home city or a random one.
    
    Args:
        home_city (str): The city associated with the user.
        config (dict): The loaded bank_configuration.json.
        
    Returns:
        str: The city name where the transaction occurred.
    """
    chance = config['probabilities']['home_location_chance']
    if random.random() < chance:
        return home_city
    return fake.city()

# ==========================================
# --- FILE OPERATIONS ---
# ==========================================

def load_json(filename, default=None):
    """Safely loads a JSON file, returning a default value if missing."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f: return json.load(f)
    return default if default is not None else []

def save_json(filename, data):
    """Writes data to a JSON file with pretty printing."""
    with open(os.path.join(DATA_DIR, filename), 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    """
    Orchestrates the loading of the simulation state.
    
    1. Loads 'bank_configuration.json' (The Rules). Creates it if missing.
    2. Loads 'bank_metadata.json' (The State/Time).
    3. Loads all resource files (users, accounts, cards, transactions).
    
    Returns:
        dict: A comprehensive dictionary containing 'configuration', 'metadata', 
              and lists for all resources.
    """
    # 1. Load Configuration (The Rules)
    config_path = os.path.join(DATA_DIR, 'bank_configuration.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        print("⚙️ Configuration not found. Creating default 'bank_configuration.json'...")
        config = DEFAULT_CONFIG
        save_json('bank_configuration.json', config)

    # 2. Load Metadata (The State)
    metadata = load_json('bank_metadata.json', {
        "current_date": datetime.date.today().isoformat()
    })

    return {
        'configuration': config,  # Read-only rules
        'metadata': metadata,     # Mutable state (current date)
        'users': load_json('users.json', []),
        'accounts': load_json('accounts.json', []),
        'cards': load_json('cards.json', []),
        'transactions': load_json('transactions.json', [])
    }

def save_data(data):
    """
    Persists the current simulation state to disk.
    
    Note: This does NOT overwrite 'bank_configuration.json' to prevent 
    overwriting user manual edits to the rules.
    """
    save_json('bank_metadata.json', data['metadata'])
    save_json('users.json', data['users'])
    save_json('accounts.json', data['accounts'])
    save_json('cards.json', data['cards'])
    save_json('transactions.json', data['transactions'])

def read_balances(data, user_id=None):
    """
    Prints a formatted ASCII table of account balances.
    
    Args:
        data (dict): The main data object.
        user_id (str, optional): If provided, filters table for this user only.
    """
    print(f"{'USER ID':<10} | {'ACCOUNT ID':<12} | {'TYPE':<10} | {'BALANCE ($)':>12}")
    print("-" * 55)
    for acc in data['accounts']:
        if user_id and acc['user_id'] != user_id: continue
        print(f"{acc['user_id']:<10} | {acc['account_id']:<12} | {acc['type']:<10} | {acc['balance']:>12.2f}")
    print("-" * 55)
    print(f"📅 Current System Date: {data['metadata']['current_date']}")

# ==========================================
# --- GENERATORS ---
# ==========================================

def create_user(data, overrides=None):
    """
    Creates a new User entity.
    
    Args:
        data (dict): Main data dictionary.
        overrides (dict, optional): Specific properties to force (e.g. {'first_name': 'John'}).
    
    Returns:
        dict: The created user object.
    """
    uid = f"u_{get_next_id(data['users'], 'user')}"
    user = {
        "user_id": uid, "username": f"user{uid.split('_')[1]}",
        "password_hash": generate_password_hash("password123", method="pbkdf2:sha256"),
        "first_name": fake.first_name(), "last_name": fake.last_name(), "email": fake.email(),
        "city": fake.city(),
        "created_at": data['metadata']['current_date'], 
        "settings": {"theme": "light", "notifications": True}
    }
    if overrides: user.update(overrides)
    data['users'].append(user)
    return user

def create_account(data, user_id, overrides=None):
    """
    Creates a Checking Account for a user.
    Initial balance and salary are determined by 'bank_configuration.json'.
    """
    config = data['configuration']['financial']
    aid = f"acc_{get_next_id(data['accounts'], 'account')}"
    
    bal_min, bal_max = config['initial_balance_range']
    sal_min, sal_max = config['salary_range']
    
    account = {
        "account_id": aid, "user_id": user_id, "type": "CHECKING", "currency": "USD",
        "balance": round(random.uniform(bal_min, bal_max), 2),
        "salary_amount": random.randrange(sal_min, sal_max, 100), 
        "status": "ACTIVE"
    }
    if overrides: account.update(overrides)
    data['accounts'].append(account)
    return account

def create_card(data, account_id, overrides=None):
    """
    Creates a Credit Card linked to an Account.
    Spending habits and limits are determined by 'bank_configuration.json'.
    """
    config_fin = data['configuration']['financial']
    config_time = data['configuration']['time']
    config_beh = data['configuration']['behavior']
    
    cid = f"card_{get_next_id(data['cards'], 'card')}"
    current_dt = datetime.date.fromisoformat(data['metadata']['current_date'])
    
    card = {
        "card_id": cid, "account_id": account_id,
        "masked_number": f"****-****-****-{random.randint(1000,9999)}",
        "status": "ACTIVE", 
        "limit": config_fin['default_credit_limit'],
        "billing_day": random.choice(config_time['billing_cycle_options']),
        "spending_profile": random.choice(list(config_beh['spending_profiles'].keys())),
        "current_spend": 0.0,
        "issue_date": current_dt.isoformat(),
        "expiry_date": (current_dt + datetime.timedelta(days=365 * config_time['card_expiry_years'])).isoformat(),
        "last_bill_date": None
    }
    if overrides: card.update(overrides)
    data['cards'].append(card)
    return card

# ==========================================
# --- TRANSACTION LOGIC ---
# ==========================================

def create_manual_transaction(data, link_id, overrides=None):
    """
    Creates a single manual transaction (Debit or Credit).
    
    Args:
        data (dict): Main data object.
        link_id (str): The ID to charge (e.g., 'card_1' or 'acc_1').
        overrides (dict): Must include 'amount' usually. Can include 'category', 'location'.
    
    Returns:
        dict: The created transaction object, or None if validation fails.
    """
    config = data['configuration']
    is_card = link_id.startswith("card_")
    
    default_amt = config['financial']['manual_transaction_default']
    amount = float(overrides.get('amount', default_amt)) if overrides else default_amt
    
    user_city = fake.city() 
    
    # 1. Validation & User Lookup (for Location)
    if is_card:
        card = next((c for c in data['cards'] if c['card_id'] == link_id), None)
        if not card: 
            print(f"❌ Error: Card {link_id} does not exist."); return None
        
        if card['current_spend'] + abs(amount) > card['limit']:
            print(f"⛔ Declined: Credit Limit Exceeded! (Limit: {card['limit']}, Current: {card['current_spend']})")
            return None
            
        account_id = card['account_id']
        card_id = link_id
        
        acc = next((a for a in data['accounts'] if a['account_id'] == account_id), None)
        if acc:
            user = next((u for u in data['users'] if u['user_id'] == acc['user_id']), None)
            if user: user_city = user['city']
    else:
        acc = next((a for a in data['accounts'] if a['account_id'] == link_id), None)
        if not acc:
            print(f"❌ Error: Account {link_id} does not exist."); return None
        account_id = link_id
        card_id = None
        user = next((u for u in data['users'] if u['user_id'] == acc['user_id']), None)
        if user: user_city = user['city']

    # 2. Record Creation
    txn_num = get_next_id(data['transactions'], 'transaction')
    cat = overrides.get('category', pick_weighted_category(config) if is_card else "Misc")
    loc = overrides.get('location', pick_location(user_city, config))

    txn = {
        "transaction_id": f"txn_{txn_num}",
        "account_id": account_id,
        "card_id": card_id,
        "amount": amount,
        "date": data['metadata']['current_date'],
        "description": "Manual Transaction",
        "category": cat,
        "location": loc,
        "type": "DEBIT" if amount < 0 else "CREDIT"
    }
    if overrides: txn.update(overrides)

    # 3. Update Balances
    if is_card:
        card['current_spend'] += abs(amount)
        print(f"💳 Swiped Card {card_id}. Debt: {card['current_spend']:.2f}/{card['limit']}")
    else:
        acc = next((a for a in data['accounts'] if a['account_id'] == account_id), None)
        acc['balance'] += amount
        print(f"💰 Account {account_id} updated. New Balance: ${acc['balance']:.2f}")
    
    data['transactions'].append(txn)
    return txn

def create_transfer_transaction(data, sender_id, receiver_id, overrides=None):
    """
    Executes a money transfer between two accounts using Double Entry logic.
    Creates TWO transaction records (Debit for sender, Credit for receiver) linked by a group ID.
    
    Args:
        sender_id (str): Account ID sending money.
        receiver_id (str): Account ID receiving money.
        overrides (dict): Optional amount/description.
    """
    config = data['configuration']
    sender = next((a for a in data['accounts'] if a['account_id'] == sender_id), None)
    receiver = next((a for a in data['accounts'] if a['account_id'] == receiver_id), None)
    
    if not sender: print(f"❌ Error: Sender Account {sender_id} not found."); return None
    if not receiver: print(f"❌ Error: Receiver Account {receiver_id} not found."); return None

    default_amt = config['financial']['transfer_default_amount']
    raw_amount = float(overrides.get('amount', default_amt)) if overrides else default_amt
    amount = abs(raw_amount)

    sender['balance'] -= amount
    receiver['balance'] += amount
    
    print(f"💸 Transferring ${amount:.2f} from {sender_id} to {receiver_id}...")

    txn_num = get_next_id(data['transactions'], 'transaction')
    date_str = data['metadata']['current_date']
    grp_id = f"grp_manual_{txn_num}"
    
    txn_out = {
        "transaction_id": f"txn_{txn_num}",
        "account_id": sender_id, "card_id": None,
        "amount": -amount, "date": date_str,
        "description": f"Transfer to {receiver_id}",
        "category": "Transfer", 
        "location": "Online Banking",
        "type": "DEBIT", "transfer_group_id": grp_id
    }
    
    txn_in = {
        "transaction_id": f"txn_{txn_num+1}",
        "account_id": receiver_id, "card_id": None,
        "amount": amount, "date": date_str,
        "description": f"Transfer from {sender_id}",
        "category": "Transfer", 
        "location": "Online Banking",
        "type": "CREDIT", "transfer_group_id": grp_id
    }
    
    if overrides:
        if 'description' in overrides:
            txn_out['description'] = overrides['description'] + " (Out)"
            txn_in['description'] = overrides['description'] + " (In)"

    data['transactions'].append(txn_out)
    data['transactions'].append(txn_in)
    
    print(f"✅ Transfer Complete. {sender_id}: ${sender['balance']:.2f} | {receiver_id}: ${receiver['balance']:.2f}")
    return [txn_out, txn_in]

# ==========================================
# --- SIMULATION ENGINE ---
# ==========================================

def simulate_days(data, days_to_add, process_only=False):
    """
    Advances the simulation clock by N days.
    
    Features:
    - Pays Salary on configured 'payroll_days'.
    - Generates spending transactions based on User Spending Profiles (Normal Distribution).
    - Pays Credit Card Bills on 'billing_day'.
    
    Args:
        data (dict): Main data object.
        days_to_add (int): Number of days to simulate.
        process_only (bool): If True, only processes payroll/bills, no random spending.
    """
    config = data['configuration']
    spending_profiles = config['behavior']['spending_profiles']
    payroll_days = config['time']['payroll_days']

    start_date = datetime.date.fromisoformat(data['metadata']['current_date'])
    end_date = start_date + datetime.timedelta(days=days_to_add)
    print(f"⏳ Advancing from {start_date} to {end_date}...")
    
    txn_num = get_next_id(data['transactions'], 'transaction')
    current_date = start_date

    while current_date < end_date:
        current_date += datetime.timedelta(days=1)
        day_str = current_date.isoformat()
        
        for acc in data['accounts']:
            user = next((u for u in data['users'] if u['user_id'] == acc['user_id']), None)
            user_city = user['city'] if user else fake.city()

            # --- Payroll Logic ---
            if current_date.day in payroll_days:
                amt = acc.get('salary_amount', 3000) / len(payroll_days)
                acc['balance'] += amt
                employer = get_consistent_company(acc['user_id'])
                data['transactions'].append({
                    "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                    "amount": amt, "date": day_str, 
                    "description": f"Payroll - {employer}", 
                    "category": "Income", 
                    "location": "Direct Deposit",
                    "type": "CREDIT", "card_id": None
                })
                txn_num += 1
            
            # --- Spending Logic ---
            linked_cards = [c for c in data['cards'] if c['account_id'] == acc['account_id']]
            for card in linked_cards:
                if not process_only:
                    habit = spending_profiles.get(card.get('spending_profile', 'AVERAGE'))
                    
                    if random.random() < habit['prob']:
                        raw_amt = random.gauss(habit['mean'], habit['std'])
                        amt = max(habit['min'], min(habit['max'], raw_amt))
                        amt = round(amt, 2)
                        
                        if card['current_spend'] + amt <= card['limit']:
                            card['current_spend'] += amt
                            selected_cat = pick_weighted_category(config)
                            selected_loc = pick_location(user_city, config)

                            data['transactions'].append({
                                "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                                "amount": -amt, "date": day_str, 
                                "description": fake.company(), 
                                "category": selected_cat, 
                                "location": selected_loc,
                                "type": "DEBIT", "card_id": card['card_id']
                            })
                            txn_num += 1
                
                # --- Billing Logic ---
                if current_date.day == card.get('billing_day', 10) and card['current_spend'] > 0:
                    bill = round(card['current_spend'], 2)
                    acc['balance'] -= bill
                    data['transactions'].append({
                        "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                        "amount": -bill, "date": day_str, 
                        "description": f"Credit Card Bill (Cycle Day {card.get('billing_day')})", 
                        "category": "Bills", 
                        "location": "Online Payment",
                        "type": "DEBIT", "card_id": None
                    })
                    txn_num += 1
                    card['current_spend'] = 0.0
                    card['last_bill_date'] = day_str
    
    data['metadata']['current_date'] = end_date.isoformat()
    print(f"✅ World Date updated to: {data['metadata']['current_date']}")

# ==========================================
# --- MAIN CLI HANDLER ---
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="Mock Banking Data Generator v2.0\n-----------------------------------\nA tool to generate realistic banking data including Users, Accounts, Cards, and Transactions.\nUse this tool to initialize a world, simulate the passage of time, or manually insert data.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
            Usage Examples:
            -----------------------------------
            1. Initialize a new world with 5 random users:
               python data_gen.py --init

            2. Advance the world clock by 30 days (generates salaries, bills, spending):
               python data_gen.py --evolve 30

            3. Check all user balances:
               python data_gen.py --balance

            4. Manually create a user:
               python data_gen.py --create user --props '{"first_name": "Alice", "city": "New York"}'

            5. Manually create a transaction (Lunch):
               python data_gen.py --create transaction --link card_1 --props '{"amount": -25.50, "category": "Food & Dining"}'
        """)
    )
    
    # --- Simulation Control Group ---
    sim_group = parser.add_argument_group('Simulation Control')
    sim_group.add_argument('--init', action='store_true', help="Wipe all existing data and create a fresh world with 5 initial users.")
    sim_group.add_argument('--start-date', metavar='YYYY-MM-DD', help="Set a specific start date when using --init (Default: Today).")
    sim_group.add_argument('--evolve', type=int, metavar='DAYS', help="Advance the world simulation by N days. Triggers payroll, spending, and bills.")
    sim_group.add_argument('--process-only', action='store_true', help="When evolving, only process mandatory events (Payroll/Bills). Skip random discretionary spending.")

    # --- Resource Management Group ---
    res_group = parser.add_argument_group('Resource Management')
    res_group.add_argument('--create', choices=['user', 'account', 'card', 'transaction'], help="Create a specific resource type manually.")
    res_group.add_argument('--link', metavar='ID', help="The Parent ID required when creating dependent resources.\n(e.g., --link card_1 when creating a transaction, or --link user_1 when creating an account).")
    res_group.add_argument('--to', metavar='ACC_ID', help="The Receiver Account ID. Required only when creating a transfer transaction.")
    res_group.add_argument('--props', metavar='JSON', help="A JSON string to override default properties of the created resource.\nExample: --props '{\"amount\": -50.00, \"description\": \"Dinner\"}'")
    res_group.add_argument('--add-users', type=int, metavar='N', help="Batch create N new users (and their associated accounts/cards).")
    res_group.add_argument('--add-resources', action='store_true', help="Randomly add new accounts/cards to existing users to simulate growth.")

    # --- Utility Group ---
    util_group = parser.add_argument_group('Utility')
    util_group.add_argument('--balance', nargs='?', const='all', metavar='USER_ID', help="Display a balance sheet. Leave empty for all users, or specify a User ID.")

    args = parser.parse_args()
    data = load_data() 

    overrides = {}
    if args.props:
        try: overrides = json.loads(args.props)
        except: print("❌ Invalid JSON in --props"); return

    if args.init:
        print("🌍 Wiping world...")
        start_date_str = datetime.date.today().isoformat()
        if args.start_date: start_date_str = args.start_date
        
        data['users'] = []
        data['accounts'] = []
        data['cards'] = []
        data['transactions'] = []
        data['metadata'] = {"current_date": start_date_str}

        for _ in range(5):
            u = create_user(data); a = create_account(data, u['user_id']); create_card(data, a['account_id'])
        save_data(data)
        simulate_days(data, 30)

    elif args.add_users:
        for _ in range(args.add_users): u = create_user(data); a = create_account(data, u['user_id']); create_card(data, a['account_id'])
        print(f"Added {args.add_users} users")

    elif args.add_resources:
        for u in data['users']: 
            if random.random() < 0.5: create_account(data, u['user_id'])
        print("Added resources")

    elif args.create == 'transaction':
        if not args.link: print("❌ Error: --link is required."); return
        if args.to:
            create_transfer_transaction(data, args.link, args.to, overrides)
        else:
            create_manual_transaction(data, args.link, overrides)

    elif args.create == 'user':
        u = create_user(data, overrides); print(f"Created {u['user_id']}")
    elif args.create == 'account':
        create_account(data, args.link, overrides); print("Created Account")
    elif args.create == 'card':
        create_card(data, args.link, overrides); print("Created Card")
    
    if args.evolve:
        simulate_days(data, args.evolve, process_only=args.process_only)

    if args.balance:
        read_balances(data, args.balance if args.balance != 'all' else None)

    save_data(data)

if __name__ == "__main__":
    main()