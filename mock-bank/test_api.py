import unittest
import json
import os
import shutil
import sys
from werkzeug.security import generate_password_hash

# Ensure we can import from root
sys.path.append(os.getcwd())

from app import create_app
from data_gen import JsonRepository

# Config
TEST_DB_DIR = 'test_api_data'

class TestBankingAPI(unittest.TestCase):

    def setUp(self):
        """
        Runs before EACH test.
        1. Setup temp data folder.
        2. Create Flask app with TEST config.
        3. Seed data.
        """
        # 1. Setup Temp Directory
        if os.path.exists(TEST_DB_DIR):
            try: shutil.rmtree(TEST_DB_DIR)
            except OSError: pass
        os.makedirs(TEST_DB_DIR)

        # 2. Seed Initial Data using DataGen Repository
        self.repo = JsonRepository(TEST_DB_DIR)
        
        self.test_user = {
            "user_id": "u_test",
            "username": "tester",
            "password_hash": generate_password_hash("password123"),
            "first_name": "QA", "last_name": "Engineer", "email": "qa@test.com",
            "city": "Testville", "created_at": "2023-01-01", "settings": {"theme": "dark"}
        }
        
        self.test_account = {
            "account_id": "acc_test", "user_id": "u_test",
            "type": "CHECKING", "currency": "USD", "balance": 5000.00, "status": "ACTIVE"
        }

        # Helper class to mimic Objects for the repo
        class MockObj:
            def __init__(self, d): self.__dict__ = d

        self.repo.save_all(
            users=[MockObj(self.test_user)], 
            accounts=[MockObj(self.test_account)],
            cards=[], acc_txns=[], card_txns=[],
            metadata={"current_date": "2023-01-01"}
        )

        # 3. Create App & Override Config
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['DATA_DIR'] = TEST_DB_DIR  # Point app to test folder
        self.client = self.app.test_client()

    def tearDown(self):
        """Cleanup after tests."""
        if os.path.exists(TEST_DB_DIR):
            try: shutil.rmtree(TEST_DB_DIR)
            except OSError: pass

    # ==========================================
    # --- AUTHENTICATION TESTS ---
    # ==========================================

    def test_login_success(self):
        payload = {"username": "tester", "password": "password123"}
        response = self.client.post('/login', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.get_json())

    def test_login_failure(self):
        payload = {"username": "tester", "password": "wrongpassword"}
        response = self.client.post('/login', json=payload)
        self.assertEqual(response.status_code, 401)

    # ==========================================
    # --- RESOURCE TESTS ---
    # ==========================================

    def get_auth_header(self):
        resp = self.client.post('/login', json={"username": "tester", "password": "password123"})
        token = resp.get_json()['token']
        return {'Authorization': f'Bearer {token}'}

    def test_get_user_profile(self):
        headers = self.get_auth_header()
        response = self.client.get('/users/u_test', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['email'], 'qa@test.com')

    def test_get_user_accounts(self):
        headers = self.get_auth_header()
        response = self.client.get('/users/u_test/accounts', headers=headers)
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['accounts']), 1)
        self.assertEqual(data['accounts'][0]['account_id'], 'acc_test')

    def test_access_denied_other_user(self):
        """Ensure User A cannot see User B."""
        headers = self.get_auth_header()
        response = self.client.get('/users/u_admin', headers=headers)
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()