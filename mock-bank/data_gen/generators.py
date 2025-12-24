import random
import datetime
from faker import Faker
from werkzeug.security import generate_password_hash
from .utils import get_next_id

fake = Faker()

def create_user(data, overrides=None):
    """
    Creates a new User entity and adds it to the simulation data.
    """
    uid = f"u_{get_next_id(data['users'], 'user')}"
    
    user = {
        "user_id": uid,
        "username": f"user{uid.split('_')[1]}",
        "password_hash": generate_password_hash("password123", method="pbkdf2:sha256"),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "city": fake.city(),
        "created_at": data['metadata']['current_date'],
        "settings": {
            "theme": "light",
            "notifications": True
        }
    }
    
    if overrides:
        user.update(overrides)
        
    data['users'].append(user)
    return user

def create_account(data, user_id, overrides=None):
    """
    Creates a CHECKING account for a user.
    Initial balance and salary are determined by the configuration rules.
    """
    config = data['configuration']['financial']
    aid = f"acc_{get_next_id(data['accounts'], 'account')}"
    
    bal_min, bal_max = config['initial_balance_range']
    sal_min, sal_max = config['salary_range']
    
    account = {
        "account_id": aid,
        "user_id": user_id,
        "type": "CHECKING",
        "currency": "USD",
        "balance": round(random.uniform(bal_min, bal_max), 2),
        "salary_amount": random.randrange(sal_min, sal_max, 100),
        "status": "ACTIVE"
    }
    
    if overrides:
        account.update(overrides)
        
    data['accounts'].append(account)
    return account

def create_card(data, account_id, overrides=None):
    """
    Creates a Credit Card linked to an existing Account.
    Sets spending profiles and calculated expiry dates.
    """
    config_fin = data['configuration']['financial']
    config_time = data['configuration']['time']
    config_beh = data['configuration']['behavior']
    
    cid = f"card_{get_next_id(data['cards'], 'card')}"
    current_dt = datetime.date.fromisoformat(data['metadata']['current_date'])
    
    card = {
        "card_id": cid,
        "account_id": account_id,
        "masked_number": f"****-****-****-{random.randint(1000, 9999)}",
        "status": "ACTIVE",
        "limit": config_fin['default_credit_limit'],
        "billing_day": random.choice(config_time['billing_cycle_options']),
        "spending_profile": random.choice(list(config_beh['spending_profiles'].keys())),
        "current_spend": 0.0,
        "issue_date": current_dt.isoformat(),
        "expiry_date": (current_dt + datetime.timedelta(days=365 * config_time['card_expiry_years'])).isoformat(),
        "last_bill_date": None
    }
    
    if overrides:
        card.update(overrides)
        
    data['cards'].append(card)
    return card