import unittest
import os
import shutil
import json
import sys
import datetime

# Ensure we can import the local module from the root directory
sys.path.append(os.getcwd())

# --- UPDATED IMPORTS (From 'data_gen' package) ---
try:
    from data_gen import (
        BankingSimulation, 
        JsonRepository, 
        process_transfer, 
        process_manual_transaction,
        run_simulation_loop
    )
except ImportError as e:
    print("❌ Critical Test Error: Could not import 'data_gen'.")
    print(f"Details: {e}")
    print("Ensure you are running this from the root folder containing the 'data_gen' directory.")
    sys.exit(1)

# Config for test environment
TEST_DIR = 'test_mock_data'

class TestBankingSimulation(unittest.TestCase):

    def setUp(self):
        """
        Runs BEFORE every test.
        Sets up a fresh BankingSimulation using a temporary directory.
        """
        # 1. Clean start
        if os.path.exists(TEST_DIR):
            try: shutil.rmtree(TEST_DIR)
            except OSError: pass
            
        os.makedirs(TEST_DIR)

        # 2. Initialize System with Test Repo
        self.repo = JsonRepository(TEST_DIR)
        self.sim = BankingSimulation(self.repo)
        
        # 3. Load (creates default empty files in test dir)
        self.sim.load_world()

    def tearDown(self):
        """
        Runs AFTER every test.
        Cleans up the temporary directory.
        """
        if os.path.exists(TEST_DIR):
            try:
                shutil.rmtree(TEST_DIR)
            except OSError as e:
                print(f"Warning: Could not clean up test dir: {e}")

    # ==========================================
    # --- CORE RESOURCE TESTS ---
    # ==========================================

    def test_create_user_and_resources(self):
        """Test the creation hierarchy: User -> Account -> Card"""
        # 1. Create User
        user = self.sim.create_user(overrides={"first_name": "Test", "last_name": "User"})
        self.assertEqual(len(self.sim.users), 1)
        self.assertEqual(user.first_name, "Test")
        self.assertTrue(user.user_id.startswith("u_"))

        # 2. Create Account linked to User
        acct = self.sim.create_account(user.user_id, overrides={"balance": 1000.00})
        self.assertEqual(len(self.sim.accounts), 1)
        self.assertEqual(acct.owner.user_id, user.user_id)
        self.assertAlmostEqual(acct.balance, 1000.00, places=2)

        # 3. Create Card linked to Account
        card = self.sim.create_card(acct.account_id, overrides={"limit": 500.00})
        self.assertEqual(len(self.sim.cards), 1)
        self.assertEqual(card.linked_account.account_id, acct.account_id)
        self.assertAlmostEqual(card.limit, 500.00, places=2)

    def test_persistence(self):
        """Test that data is correctly saved to JSON and reloaded."""
        u = self.sim.create_user(overrides={"username": "save_test"})
        self.sim.create_account(u.user_id)
        
        self.sim.save_world()

        # Create a NEW simulation instance and load from the same disk location
        new_sim = BankingSimulation(self.repo)
        new_sim.load_world()

        self.assertEqual(len(new_sim.users), 1)
        self.assertEqual(new_sim.users[0].username, "save_test")
        self.assertEqual(len(new_sim.accounts), 1)
        # Verify relationship restoration
        self.assertEqual(new_sim.accounts[0].owner.username, "save_test")

    # ==========================================
    # --- TRANSACTION TESTS ---
    # ==========================================

    def test_account_transfer(self):
        """Test money movement between two accounts (Double Entry)."""
        u1 = self.sim.create_user()
        a1 = self.sim.create_account(u1.user_id, overrides={"balance": 500.00})
        
        u2 = self.sim.create_user()
        a2 = self.sim.create_account(u2.user_id, overrides={"balance": 100.00})

        process_transfer(self.sim, a1.account_id, a2.account_id, overrides={"amount": 50.00})

        self.assertAlmostEqual(a1.balance, 450.00, places=2)
        self.assertAlmostEqual(a2.balance, 150.00, places=2)
        
        # Check Ledger
        self.assertEqual(len(self.sim.account_txns), 2)
        self.assertEqual(self.sim.account_txns[0]['transfer_group_id'], self.sim.account_txns[1]['transfer_group_id'])

    def test_manual_transaction(self):
        """Test manual Credit and Debit operations."""
        u = self.sim.create_user()
        a = self.sim.create_account(u.user_id, overrides={"balance": 100.00})

        # 1. Credit (Add Money)
        process_manual_transaction(self.sim, a.account_id, overrides={"amount": 50.00, "description": "Deposit"})
        self.assertAlmostEqual(a.balance, 150.00, places=2)

        # 2. Debit (Remove Money)
        process_manual_transaction(self.sim, a.account_id, overrides={"amount": -25.00, "description": "Withdrawal"})
        self.assertAlmostEqual(a.balance, 125.00, places=2)

        self.assertEqual(len(self.sim.account_txns), 2)

    def test_invalid_transfer(self):
        """Ensure transfers fail gracefully with bad IDs."""
        process_transfer(self.sim, "bad_id_1", "bad_id_2", overrides={"amount": 100})
        # Should not crash, and should not record transactions
        self.assertEqual(len(self.sim.account_txns), 0)

    # ==========================================
    # --- CARD LOGIC TESTS ---
    # ==========================================

    def test_credit_card_lifecycle(self):
        """Test Charging -> Limit Check -> Bill Payment"""
        u = self.sim.create_user()
        a = self.sim.create_account(u.user_id, overrides={"balance": 2000.00})
        c = self.sim.create_card(a.account_id, overrides={"limit": 1000.00, "billing_day": 15})

        # 1. Charge Card (Success)
        c.charge(200.00, "Groceries", "Food", "Store", "2023-01-01")
        self.assertAlmostEqual(c.current_spend, 200.00, places=2)

        # 2. Charge Card (Fail - Over Limit)
        result = c.charge(900.00, "Luxury Item", "Shopping", "Mall", "2023-01-02")
        self.assertIsNone(result) 
        self.assertAlmostEqual(c.current_spend, 200.00, places=2)

        # 3. Pay Bill
        c.pay_bill("2023-01-15")
        self.assertAlmostEqual(c.current_spend, 0.00, places=2)
        self.assertAlmostEqual(a.balance, 1800.00, places=2) # 2000 - 200

    # ==========================================
    # --- SIMULATION ENGINE TESTS ---
    # ==========================================

    def test_simulation_payroll(self):
        """Test that advancing time triggers payroll on the 1st or 15th."""
        # 1. Setup world on the day BEFORE payroll
        # Default config payroll is 1st and 15th.
        self.sim.metadata['current_date'] = "2023-01-14" 
        
        u = self.sim.create_user()
        a = self.sim.create_account(u.user_id, overrides={"balance": 0.00, "salary_amount": 3000})
        
        # 2. Advance by 2 days (crossing the 15th)
        run_simulation_loop(self.sim, days=2, process_only=True)
        
        # 3. Check Date
        self.assertEqual(self.sim.metadata['current_date'], "2023-01-16")
        
        # 4. Check Balance
        # Salary is 3000, split into 2 payments = 1500 per pay period
        self.assertAlmostEqual(a.balance, 1500.00, places=2)
        
        # 5. Check Transaction Log
        self.assertEqual(len(self.sim.account_txns), 1)
        self.assertIn("Payroll", self.sim.account_txns[0]['description'])

if __name__ == '__main__':
    unittest.main()