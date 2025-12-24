import datetime
import random
from faker import Faker
from .utils import (
    get_next_id, 
    get_consistent_company, 
    pick_weighted_category, 
    pick_location
)

fake = Faker()

# ==========================================
# --- TRANSACTION LOGIC ---
# ==========================================

def create_manual_transaction(data, link_id, overrides=None):
    """
    Creates a single manual transaction (Debit or Credit).
    Updates account balances or credit card spending accordingly.
    """
    config = data['configuration']
    is_card = link_id.startswith("card_")
    
    default_amt = config['financial']['manual_transaction_default']
    amount = float(overrides.get('amount', default_amt)) if overrides else default_amt
    
    # 1. Validation & Resource Lookup
    user_city = "Unknown"
    if is_card:
        card = next((c for c in data['cards'] if c['card_id'] == link_id), None)
        if not card:
            print(f"Error: Card {link_id} not found."); return None
        
        if card['current_spend'] + abs(amount) > card['limit']:
            print(f"Declined: Credit Limit Exceeded for {link_id}")
            return None
            
        account_id = card['account_id']
        card_id = link_id
        acc = next((a for a in data['accounts'] if a['account_id'] == account_id), None)
    else:
        acc = next((a for a in data['accounts'] if a['account_id'] == link_id), None)
        if not acc:
            print(f"Error: Account {link_id} not found."); return None
        account_id = link_id
        card_id = None

    # Determine location for the transaction
    if acc:
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
        "description": overrides.get('description', "Manual Transaction"),
        "category": cat,
        "location": loc,
        "type": "DEBIT" if amount < 0 else "CREDIT"
    }
    if overrides: txn.update(overrides)

    # 3. Update State
    if is_card:
        card['current_spend'] += abs(amount)
    else:
        acc['balance'] += amount
    
    data['transactions'].append(txn)
    return txn

def create_transfer_transaction(data, sender_id, receiver_id, overrides=None):
    """
    Executes a transfer between two accounts.
    Creates two linked transaction records (Double Entry).
    """
    config = data['configuration']
    sender = next((a for a in data['accounts'] if a['account_id'] == sender_id), None)
    receiver = next((a for a in data['accounts'] if a['account_id'] == receiver_id), None)
    
    if not sender or not receiver:
        print("Error: Invalid sender or receiver ID."); return None

    default_amt = config['financial']['transfer_default_amount']
    amount = abs(float(overrides.get('amount', default_amt)) if overrides else default_amt)

    # Update Balances
    sender['balance'] -= amount
    receiver['balance'] += amount

    txn_num = get_next_id(data['transactions'], 'transaction')
    date_str = data['metadata']['current_date']
    grp_id = f"grp_{txn_num}"
    
    txn_out = {
        "transaction_id": f"txn_{txn_num}",
        "account_id": sender_id, "card_id": None,
        "amount": -amount, "date": date_str,
        "description": f"Transfer to {receiver_id}",
        "category": "Transfer", "location": "Online Banking",
        "type": "DEBIT", "transfer_group_id": grp_id
    }
    
    txn_in = {
        "transaction_id": f"txn_{txn_num + 1}",
        "account_id": receiver_id, "card_id": None,
        "amount": amount, "date": date_str,
        "description": f"Transfer from {sender_id}",
        "category": "Transfer", "location": "Online Banking",
        "type": "CREDIT", "transfer_group_id": grp_id
    }

    data['transactions'].extend([txn_out, txn_in])
    return [txn_out, txn_in]

# ==========================================
# --- SIMULATION ENGINE ---
# ==========================================

def simulate_days(data, days_to_add, process_only=False):
    """
    Advances the world clock by N days.
    Simulates payroll, discretionary spending, and monthly bills.
    """
    config = data['configuration']
    spending_profiles = config['behavior']['spending_profiles']
    payroll_days = config['time']['payroll_days']

    start_date = datetime.date.fromisoformat(data['metadata']['current_date'])
    end_date = start_date + datetime.timedelta(days=days_to_add)
    
    print(f"Simulating from {start_date} to {end_date}...")
    
    txn_num = get_next_id(data['transactions'], 'transaction')
    current_date = start_date

    while current_date < end_date:
        current_date += datetime.timedelta(days=1)
        day_str = current_date.isoformat()
        
        for acc in data['accounts']:
            user = next((u for u in data['users'] if u['user_id'] == acc['user_id']), None)
            user_city = user['city'] if user else fake.city()

            # 1. Payroll Logic
            if current_date.day in payroll_days:
                amt = acc.get('salary_amount', 3000) / len(payroll_days)
                acc['balance'] += amt
                employer = get_consistent_company(acc['user_id'])
                data['transactions'].append({
                    "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                    "amount": amt, "date": day_str, "description": f"Payroll - {employer}",
                    "category": "Income", "location": "Direct Deposit",
                    "type": "CREDIT", "card_id": None
                })
                txn_num += 1
            
            # 2. Card Logic (Spending & Billing)
            linked_cards = [c for c in data['cards'] if c['account_id'] == acc['account_id']]
            for card in linked_cards:
                # Random Spending based on habit profile
                if not process_only:
                    habit = spending_profiles.get(card.get('spending_profile', 'AVERAGE'))
                    if random.random() < habit['prob']:
                        raw_amt = random.gauss(habit['mean'], habit['std'])
                        amt = round(max(habit['min'], min(habit['max'], raw_amt)), 2)
                        
                        if card['current_spend'] + amt <= card['limit']:
                            card['current_spend'] += amt
                            data['transactions'].append({
                                "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                                "amount": -amt, "date": day_str, "description": fake.company(),
                                "category": pick_weighted_category(config), 
                                "location": pick_location(user_city, config),
                                "type": "DEBIT", "card_id": card['card_id']
                            })
                            txn_num += 1

                # Monthly Billing Logic
                if current_date.day == card.get('billing_day', 10) and card['current_spend'] > 0:
                    bill = round(card['current_spend'], 2)
                    acc['balance'] -= bill
                    data['transactions'].append({
                        "transaction_id": f"txn_{txn_num}", "account_id": acc['account_id'],
                        "amount": -bill, "date": day_str, 
                        "description": f"Credit Card Bill Payment",
                        "category": "Bills", "location": "Online Payment",
                        "type": "DEBIT", "card_id": None
                    })
                    txn_num += 1
                    card['current_spend'] = 0.0
                    card['last_bill_date'] = day_str
    
    data['metadata']['current_date'] = end_date.isoformat()
    print(f"Simulation complete. World date is now {data['metadata']['current_date']}")