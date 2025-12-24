import requests
import json

BASE_URL = "http://127.0.0.1:5000"
USER_CREDENTIALS = {
    "username": "user1",
    "password": "password123"
}

def run_tests():
    print(f"🚀 Starting API Integration Tests at {BASE_URL}\n")
    token = None

    # 1. Test Login
    print("Test 1: Login...")
    response = requests.post(f"{BASE_URL}/login", json=USER_CREDENTIALS)
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"✅ Login successful. Token received.")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Get Profile
    print("\nTest 2: Get User Profile...")
    response = requests.get(f"{BASE_URL}/users/u_1", headers=headers)
    if response.status_code == 200:
        print(f"✅ Profile received: {response.json().get('first_name')} {response.json().get('last_name')}")
    else:
        print(f"❌ Failed to get profile: {response.status_code}")

    # 3. Test Get Accounts
    print("\nTest 3: List Accounts...")
    response = requests.get(f"{BASE_URL}/users/u_1/accounts", headers=headers)
    if response.status_code == 200:
        data = response.json()
        
        # --- Debugging (Optional: uncomment to see the structure) ---
        # print(f"DEBUG: Data type is {type(data)}. Content: {data}")
        # -----------------------------------------------------------

        # Normalize data to a flat list
        if isinstance(data, dict):
            accounts_list = list(data.values())
        else:
            accounts_list = data

        print(f"✅ Found {len(accounts_list)} items in accounts response.")

        if len(accounts_list) > 0:
            first_item = accounts_list[0]
            
            # Defensive check: if the first item is a list, take its first element
            if isinstance(first_item, list) and len(first_item) > 0:
                first_account = first_item[0]
            else:
                first_account = first_item

            # Now we should safely have a dictionary
            if isinstance(first_account, dict):
                acc_id = first_account.get('account_id')
                print(f"✅ Identified Account ID: {acc_id}")
                
                # 4. Test Get Transactions
                print(f"\nTest 4: Get Transactions for {acc_id}...")
                tx_res = requests.get(f"{BASE_URL}/accounts/{acc_id}/transactions", headers=headers)
                if tx_res.status_code == 200:
                    tx_data = tx_res.json()
                    tx_count = len(tx_data) if isinstance(tx_data, (list, dict)) else 0
                    print(f"✅ Found {tx_count} transactions.")
            else:
                print(f"❌ Error: Account data format unexpected. Found: {type(first_account)}")

    # 5. Test Unauthorized Access
    print("\nTest 5: Unauthorized Access (Negative Test)...")
    bad_res = requests.get(f"{BASE_URL}/users/u_1/accounts")
    if bad_res.status_code == 401:
        print("✅ Correct: Access denied without token.")
    else:
        print(f"❌ Fail: Access should have been denied but got {bad_res.status_code}")

    print("\n--- Tests Complete ---")

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to the API at {BASE_URL}. Is the server running?")