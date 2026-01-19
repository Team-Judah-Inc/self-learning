import os
import sys
import datetime
from config import Config
from data_gen import BankingSimulation, SqlRepository, JsonRepository, run_simulation_loop

def run_job():
    print("🚀 Starting Banking Simulation Job...")
    
    # 1. Setup Repository
    if Config.DB_TYPE == 'sqlite' or 'sql' in Config.DB_TYPE:
        print(f"Using SQL Repository ({Config.SQLALCHEMY_DATABASE_URI})")
        repo = SqlRepository(Config.SQLALCHEMY_DATABASE_URI)
    else:
        print(f"Using JSON Repository ({Config.DATA_DIR})")
        repo = JsonRepository(Config.DATA_DIR)
        
    bank = BankingSimulation(repo)
    
    # 2. Load World
    try:
        bank.load_world()
        print(f"Loaded world with {len(bank.users)} users.")
    except Exception as e:
        print(f"Error loading world: {e}")
        # If load fails, we might need to initialize
        bank.users = []

    # 3. Initialize if empty
    if not bank.users:
        print("⚠️ World is empty. Initializing new world...")
        bank.metadata['current_date'] = datetime.date.today().isoformat()
        for _ in range(5):
            u = bank.create_user()
            a = bank.create_account(u.user_id)
            bank.create_card(a.account_id)
        
        # Initial history
        run_simulation_loop(bank, 30)
        print("✅ World initialized.")
    
    # 4. Evolve Time (Daily Job)
    # Advance by 1 day
    print("⏳ Advancing simulation by 1 day...")
    run_simulation_loop(bank, 1)
    
    # 5. Save State
    bank.save_world()
    print("💾 World state saved.")
    print("✅ Job Complete.")

if __name__ == "__main__":
    run_job()