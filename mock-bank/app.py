from flask import Flask, jsonify, abort, request
from functools import wraps
import json
import os
import jwt
import datetime
from werkzeug.security import check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger  # <--- IMPORT FLASGGER

app = Flask(__name__)

# --- CONFIGURATION ---
DATA_DIR = 'mock_data'
SECRET_KEY = os.environ.get("JWT_SECRET", "dev_secret_key")

# Limits
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

# --- SWAGGER CONFIGURATION ---
# This configures the "Authorize" button in the UI to accept Bearer tokens
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Banking API",
        "description": "A mock banking API with JWT Authentication and Rate Limiting",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter your bearer token in the format **Bearer &lt;token&gt;**"
        }
    },
    "security": [
        {"Bearer": []}
    ]
}

swagger = Swagger(app, template=swagger_template)

# Rate Limiter Setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)

# --- HELPER FUNCTIONS ---

def load_table(name):
    """Loads a JSON file from the mock_data directory."""
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(path): 
        return []
    with open(path, 'r') as f: 
        return json.load(f)

def parse_date(date_str):
    """Parses ISO date strings (YYYY-MM-DD). Returns None on failure."""
    try:
        return datetime.datetime.fromisoformat(date_str).date()
    except ValueError:
        return None

def paginate(data_list):
    """Slices a list based on 'page' and 'limit' query params."""
    try:
        limit = int(request.args.get('limit', DEFAULT_PAGE_SIZE))
        page = int(request.args.get('page', 1))
    except ValueError:
        limit = DEFAULT_PAGE_SIZE
        page = 1
    
    if limit > MAX_PAGE_SIZE: limit = MAX_PAGE_SIZE
    if limit < 1: limit = 1
    if page < 1: page = 1

    total_items = len(data_list)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    results = data_list[start_index:end_index]
    total_pages = (total_items + limit - 1) // limit if limit > 0 else 0
    
    meta = {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return results, meta

# --- AUTHENTICATION DECORATOR ---

def check_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload['user_id']
            
            users = load_table('users')
            user = next((u for u in users if u['user_id'] == user_id), None)
            
            if not user:
                return jsonify({"error": "User invalid"}), 401
                
            return f(current_user=user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
            
    return decorated_function

# --- ROUTES ---

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Exchanges credentials for a JWT Token.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: user_1
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
            user_id:
              type: string
            expires_in:
              type: integer
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid body"}), 400

    users = load_table('users')
    user = next((u for u in users if u['username'] == data.get('username')), None)
    
    if user and check_password_hash(user['password_hash'], data.get('password')):
        token = jwt.encode({
            'user_id': user['user_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({
            "token": token, 
            "user_id": user['user_id'],
            "expires_in": 3600
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/users/<user_id>', methods=['GET'])
@check_auth
def get_user(current_user, user_id):
    """
    Get User Profile.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: The ID of the user (must match token owner)
      - name: include_settings
        in: query
        type: boolean
        description: If true, returns user settings object
    responses:
      200:
        description: User details
      403:
        description: Access Denied (ID mismatch)
    """
    if current_user['user_id'] != user_id: 
        return jsonify({"error": "Access Denied"}), 403
    
    response = current_user.copy()
    del response['password_hash']
    
    if request.args.get('include_settings') != 'true': 
        response.pop('settings', None)
        
    return jsonify(response)

@app.route('/users/<user_id>/accounts', methods=['GET'])
@check_auth
def get_user_accounts(current_user, user_id):
    """
    List all accounts for a user.
    ---
    tags:
      - Accounts
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: type
        in: query
        type: string
        enum: [CHECKING, SAVINGS, CREDIT]
        description: Filter by account type
      - name: currency
        in: query
        type: string
        description: Filter by currency (e.g. USD)
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: List of accounts with pagination metadata
      403:
        description: Access Denied
    """
    if current_user['user_id'] != user_id: 
        return jsonify({"error": "Access Denied"}), 403
    
    all_accounts = load_table('accounts')
    my_accounts = [a for a in all_accounts if a['user_id'] == user_id]
    
    # Filters
    if request.args.get('type'):
        my_accounts = [a for a in my_accounts if a['type'] == request.args.get('type')]
    if request.args.get('currency'):
        my_accounts = [a for a in my_accounts if a['currency'] == request.args.get('currency')]

    # Pagination
    paginated_accounts, meta = paginate(my_accounts)
        
    return jsonify({"meta": meta, "accounts": paginated_accounts})

@app.route('/accounts/<account_id>', methods=['GET'])
@check_auth
def get_account_details(current_user, account_id):
    """
    Get details of a specific account.
    ---
    tags:
      - Accounts
    parameters:
      - name: account_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Account object
      403:
        description: Access Denied
      404:
        description: Account not found
    """
    account = next((a for a in load_table('accounts') if a['account_id'] == account_id), None)
    if not account: abort(404)
    if account['user_id'] != current_user['user_id']: 
        return jsonify({"error": "Access Denied"}), 403
    return jsonify(account)

@app.route('/accounts/<account_id>/transactions', methods=['GET'])
@check_auth
@limiter.limit("20 per minute")
def get_account_transactions(current_user, account_id):
    """
    List transactions for an account (Search & Filter).
    ---
    tags:
      - Transactions
    parameters:
      - name: account_id
        in: path
        type: string
        required: true
      - name: category
        in: query
        type: string
        description: Filter by category (e.g., Food, Transport)
      - name: search
        in: query
        type: string
        description: Search text within description
      - name: sort
        in: query
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort by date
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: List of transactions
      403:
        description: Access Denied
    """
    # Security
    account = next((a for a in load_table('accounts') if a['account_id'] == account_id), None)
    if not account or account['user_id'] != current_user['user_id']: 
        return jsonify({"error": "Access Denied"}), 403
    
    # Data & Filtering
    all_txns = load_table('transactions')
    account_txns = [t for t in all_txns if t['account_id'] == account_id]
    
    if request.args.get('category'): 
        account_txns = [t for t in account_txns if t.get('category') == request.args.get('category')]

    search_term = request.args.get('search')
    if search_term:
        account_txns = [t for t in account_txns if search_term.lower() in t['description'].lower()]
    
    # Sorting
    is_asc = request.args.get('sort') == 'asc'
    account_txns.sort(key=lambda x: x['date'], reverse=not is_asc)
    
    # Pagination
    paginated_txns, meta = paginate(account_txns)
    
    return jsonify({"account_id": account_id, "meta": meta, "transactions": paginated_txns})

@app.route('/accounts/<account_id>/cards', methods=['GET'])
@check_auth
def get_account_cards(current_user, account_id):
    """
    List cards linked to an account.
    ---
    tags:
      - Cards
    parameters:
      - name: account_id
        in: path
        type: string
        required: true
      - name: status
        in: query
        type: string
        enum: [ACTIVE, BLOCKED, EXPIRED]
    responses:
      200:
        description: List of cards
      403:
        description: Access Denied
    """
    account = next((a for a in load_table('accounts') if a['account_id'] == account_id), None)
    if not account or account['user_id'] != current_user['user_id']: 
        return jsonify({"error": "Access Denied"}), 403
        
    all_cards = load_table('cards')
    my_cards = [c for c in all_cards if c['account_id'] == account_id]
    
    if request.args.get('status'):
        my_cards = [c for c in my_cards if c['status'] == request.args.get('status')]
        
    return jsonify({"account_id": account_id, "cards": my_cards})

@app.route('/cards/<card_id>', methods=['GET'])
@check_auth
def get_card_details(current_user, card_id):
    """
    Get details of a specific card.
    ---
    tags:
      - Cards
    parameters:
      - name: card_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Card details
      403:
        description: Access Denied
      404:
        description: Card not found
    """
    card = next((c for c in load_table('cards') if c['card_id'] == card_id), None)
    if not card: abort(404)
    
    # Ownership via Account
    account = next((a for a in load_table('accounts') if a['account_id'] == card['account_id']), None)
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(card)

@app.route('/cards/<card_id>/transactions', methods=['GET'])
@check_auth
@limiter.limit("20 per minute")
def get_card_transactions(current_user, card_id):
    """
    List transactions for a specific card.
    ---
    tags:
      - Transactions
    parameters:
      - name: card_id
        in: path
        type: string
        required: true
      - name: start_date
        in: query
        type: string
        format: date
        description: YYYY-MM-DD
      - name: end_date
        in: query
        type: string
        format: date
        description: YYYY-MM-DD
      - name: min_amount
        in: query
        type: number
        description: Filter transactions with absolute amount greater than this
    responses:
      200:
        description: List of transactions
      403:
        description: Access Denied
    """
    card = next((c for c in load_table('cards') if c['card_id'] == card_id), None)
    if not card: abort(404)
    account = next((a for a in load_table('accounts') if a['account_id'] == card['account_id']), None)
    if not account or account['user_id'] != current_user['user_id']: return jsonify({"error": "Access Denied"}), 403

    card_txns = [t for t in load_table('transactions') if t.get('card_id') == card_id]

    # Filters
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    
    if start_str and parse_date(start_str):
        card_txns = [t for t in card_txns if parse_date(t['date']) >= parse_date(start_str)]
    if end_str and parse_date(end_str):
        card_txns = [t for t in card_txns if parse_date(t['date']) <= parse_date(end_str)]

    if request.args.get('min_amount'):
        limit_val = float(request.args.get('min_amount'))
        card_txns = [t for t in card_txns if abs(t['amount']) >= limit_val]

    # Pagination
    paginated_txns, meta = paginate(card_txns)

    return jsonify({"card_id": card_id, "meta": meta, "transactions": paginated_txns})

@app.route('/transactions/<transaction_id>', methods=['GET'])
@check_auth
def get_transaction_receipt(current_user, transaction_id):
    """
    Get a single transaction receipt.
    ---
    tags:
      - Transactions
    parameters:
      - name: transaction_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Transaction object
      403:
        description: Access Denied
      404:
        description: Transaction not found
    """
    txn = next((t for t in load_table('transactions') if t['transaction_id'] == transaction_id), None)
    if not txn: abort(404)
    
    account = next((a for a in load_table('accounts') if a['account_id'] == txn['account_id']), None)
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(txn)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)