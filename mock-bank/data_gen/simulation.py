import datetime
import random
from typing import List, Optional
from werkzeug.security import generate_password_hash

# --- FIX: Relative Imports ---
from .models import User, Account, Card
from .repository import DataRepository
from .utils import fake, get_consistent_company, pick_weighted_category, pick_location

class BankingSimulation:
    def __init__(self, repository: DataRepository):
        self.repo = repository
        self.users: List[User] = []
        self.accounts: List[Account] = []
        self.cards: List[Card] = []
        self.account_txns: List[dict] = []
        self.card_txns: List[dict] = []
        self.config = {}
        self.metadata = {}

    def load_world(self):
        self.config = self.repo.load_config()
        self.metadata = self.repo.load_metadata()
        raw_users, raw_accounts, raw_cards, self.account_txns, self.card_txns = self.repo.load_resources()
        
        self.users = [User(u) for u in raw_users]
        self.accounts = []
        for a in raw_accounts:
            owner = next((u for u in self.users if u.user_id == a['user_id']), None)
            if owner: self.accounts.append(Account(a, owner, self))
        self.cards = []
        for c in raw_cards:
            acc = next((a for a in self.accounts if a.account_id == c['account_id']), None)
            if acc: self.cards.append(Card(c, acc, self))

    def save_world(self):
        self.repo.save_all(self.users, self.accounts, self.cards, self.account_txns, self.card_txns, self.metadata)

    def record_account_txn(self, account_id, amount, desc, cat, loc, date, type_override, group_id):
        txn_id = self.repo.generate_id('atxn', self.account_txns)
        txn_type = type_override if type_override else ("DEBIT" if amount < 0 else "CREDIT")
        record = {
            "transaction_id": txn_id, "account_id": account_id, "amount": amount,
            "date": date, "description": desc, "category": cat,
            "location": loc, "type": txn_type
        }
        if group_id: record['transfer_group_id'] = group_id
        self.account_txns.append(record)
        return record

    def record_card_txn(self, card_id, amount, desc, cat, loc, date):
        txn_id = self.repo.generate_id('ctxn', self.card_txns)
        record = {
            "transaction_id": txn_id, "card_id": card_id, "amount": amount,
            "date": date, "description": desc, "category": cat,
            "location": loc, "type": "DEBIT"
        }
        self.card_txns.append(record)
        return record

    def create_user(self, overrides: dict = None) -> User:
        uid = self.repo.generate_id('user', self.users)
        data = {
            "user_id": uid, "username": f"user{uid.split('_')[1]}",
            "password_hash": generate_password_hash("password123", method="pbkdf2:sha256"),
            "first_name": fake.first_name(), "last_name": fake.last_name(), "email": fake.email(),
            "city": fake.city(), "created_at": self.metadata['current_date'], 
            "settings": {"theme": "light", "notifications": True}
        }
        if overrides: data.update(overrides)
        u = User(data)
        self.users.append(u)
        return u

    def create_account(self, user_id: str, overrides: dict = None) -> Optional[Account]:
        user = next((u for u in self.users if u.user_id == user_id), None)
        if not user: return None
        aid = self.repo.generate_id('account', self.accounts)
        c = self.config['financial']
        data = {
            "account_id": aid, "user_id": user_id, "type": "CHECKING", "currency": "USD",
            "balance": round(random.uniform(c['initial_balance_range'][0], c['initial_balance_range'][1]), 2),
            "salary_amount": random.randrange(c['salary_range'][0], c['salary_range'][1], 100), "status": "ACTIVE"
        }
        if overrides: data.update(overrides)
        acc = Account(data, user, self)
        self.accounts.append(acc)
        return acc

    def create_card(self, account_id: str, overrides: dict = None) -> Optional[Card]:
        acc = next((a for a in self.accounts if a.account_id == account_id), None)
        if not acc: return None
        cid = self.repo.generate_id('card', self.cards)
        cf, ct, cb = self.config['financial'], self.config['time'], self.config['behavior']
        curr_date = datetime.date.fromisoformat(self.metadata['current_date'])
        data = {
            "card_id": cid, "account_id": account_id,
            "masked_number": f"****-****-****-{random.randint(1000,9999)}",
            "status": "ACTIVE", "limit": cf['default_credit_limit'],
            "billing_day": random.choice(ct['billing_cycle_options']),
            "spending_profile": random.choice(list(cb['spending_profiles'].keys())),
            "current_spend": 0.0,
            "issue_date": curr_date.isoformat(),
            "expiry_date": (curr_date + datetime.timedelta(days=365 * ct['card_expiry_years'])).isoformat(),
            "last_bill_date": None
        }
        if overrides: data.update(overrides)
        card = Card(data, acc, self)
        self.cards.append(card)
        return card

def process_manual_transaction(sim: BankingSimulation, link_id: str, overrides: dict = None):
    config = sim.config
    amt = float(overrides.get('amount', config['financial']['manual_transaction_default'])) if overrides else config['financial']['manual_transaction_default']

    if link_id.startswith("card_"):
        card = next((c for c in sim.cards if c.card_id == link_id), None)
        if not card: print(f"❌ Error: Card {link_id} not found"); return
        txn = card.charge(amt, "Manual Swipe", overrides.get('category', pick_weighted_category(config)),
                          overrides.get('location', pick_location(card.linked_account.owner.city, config)), sim.metadata['current_date'])
        if txn: print(f"💳 Charged. New Spend: {card.current_spend:.2f}")
        else: print("⛔ Declined: Limit Exceeded")

    elif link_id.startswith("acc_"):
        acc = next((a for a in sim.accounts if a.account_id == link_id), None)
        if not acc: print(f"❌ Error: Account {link_id} not found"); return
        acc.post_transaction(amt, "Manual Op", overrides.get('category', "Misc"),
                             overrides.get('location', pick_location(acc.owner.city, config)), sim.metadata['current_date'])
        print(f"💰 Balance Adjusted: {acc.balance:.2f}")

def process_transfer(sim: BankingSimulation, sender_id: str, receiver_id: str, overrides: dict = None):
    sender = next((a for a in sim.accounts if a.account_id == sender_id), None)
    receiver = next((a for a in sim.accounts if a.account_id == receiver_id), None)
    if not sender or not receiver: print("❌ Invalid Accounts"); return

    amt = abs(float(overrides.get('amount', 50.00)) if overrides else 50.00)
    grp_id = f"grp_{sim.repo.generate_id('atxn', sim.account_txns).split('_')[1]}"
    date = sim.metadata['current_date']

    sender.post_transaction(-amt, f"Transfer to {receiver_id}", "Transfer", "Online", date, "DEBIT", grp_id)
    receiver.post_transaction(amt, f"Transfer from {sender_id}", "Transfer", "Online", date, "CREDIT", grp_id)
    print(f"✅ Transferred ${amt:.2f}")

def run_simulation_loop(sim: BankingSimulation, days: int, process_only: bool = False):
    start = datetime.date.fromisoformat(sim.metadata['current_date'])
    end = start + datetime.timedelta(days=days)
    print(f"⏳ Advancing {start} -> {end}...")

    curr = start
    while curr < end:
        curr += datetime.timedelta(days=1)
        d_str = curr.isoformat()
        
        for acc in sim.accounts:
            # Payroll
            if curr.day in sim.config['time']['payroll_days']:
                amt = acc.salary_amount / len(sim.config['time']['payroll_days'])
                acc.post_transaction(amt, f"Payroll - {get_consistent_company(acc.user_id)}", "Income", "Direct Deposit", d_str, "CREDIT")

            my_cards = [c for c in sim.cards if c.account_id == acc.account_id]
            for card in my_cards:
                # Spending
                if not process_only:
                    habit = sim.config['behavior']['spending_profiles'].get(card.spending_profile, sim.config['behavior']['spending_profiles']['AVERAGE'])
                    if random.random() < habit['prob']:
                        raw_amt = random.gauss(habit['mean'], habit['std'])
                        amt = round(max(habit['min'], min(habit['max'], raw_amt)), 2)
                        card.charge(-amt, fake.company(), pick_weighted_category(sim.config), pick_location(acc.owner.city, sim.config), d_str)
                # Bill Pay
                if curr.day == card.billing_day:
                    card.pay_bill(d_str)

    sim.metadata['current_date'] = end.isoformat()
    print("✅ Time Travel Complete.")