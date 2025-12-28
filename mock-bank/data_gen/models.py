from typing import TYPE_CHECKING
if TYPE_CHECKING: from .simulation import BankingSimulation

class BaseModel:
    def to_dict(self) -> dict: return self.__dict__

class User(BaseModel):
    def __init__(self, data: dict):
        self.user_id = data['user_id']
        self.username = data['username']
        self.password_hash = data['password_hash']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.city = data['city']
        self.created_at = data['created_at']
        self.settings = data['settings']

class Account(BaseModel):
    def __init__(self, data: dict, user: User, simulation: 'BankingSimulation'):
        self.account_id = data['account_id']
        self.user_id = data['user_id']
        self.type = data['type']
        self.currency = data['currency']
        self.balance = data['balance']
        self.salary_amount = data['salary_amount']
        self.status = data['status']
        self.owner = user
        self.sim = simulation

    def post_transaction(self, amount: float, description: str, category: str, 
                         location: str, date: str, type_override: str = None, group_id: str = None):
        self.balance += amount
        self.sim.record_account_txn(self.account_id, amount, description, category, location, date, type_override, group_id)

class Card(BaseModel):
    def __init__(self, data: dict, account: Account, simulation: 'BankingSimulation'):
        self.card_id = data['card_id']
        self.account_id = data['account_id']
        self.masked_number = data['masked_number']
        self.status = data['status']
        self.limit = data['limit']
        self.billing_day = data['billing_day']
        self.spending_profile = data['spending_profile']
        self.current_spend = data['current_spend']
        self.issue_date = data['issue_date']
        self.expiry_date = data['expiry_date']
        self.last_bill_date = data['last_bill_date']
        self.linked_account = account
        self.sim = simulation

    def charge(self, amount: float, description: str, category: str, location: str, date: str):
        if self.current_spend + abs(amount) > self.limit: return None
        self.current_spend += abs(amount)
        return self.sim.record_card_txn(self.card_id, amount, description, category, location, date)

    def pay_bill(self, date: str):
        if self.current_spend <= 0: return
        bill_amount = round(self.current_spend, 2)
        self.linked_account.post_transaction(
            -bill_amount, f"Credit Card Bill (Cycle {self.billing_day})", 
            "Bills", "Online Payment", date, type_override="DEBIT"
        )
        self.current_spend = 0.0
        self.last_bill_date = date