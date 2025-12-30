from flask import Blueprint, jsonify, request, current_app, abort
from app.utils import load_table, paginate
from app.auth import check_auth
from app import limiter

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/accounts/<account_id>', methods=['GET'])
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
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == account_id), None)
    
    if not account:
        abort(404)
        
    if account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(account)

@accounts_bp.route('/accounts/<account_id>/transactions', methods=['GET'])
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
      - name: search
        in: query
        type: string
      - name: sort
        in: query
        type: string
        enum: [asc, desc]
        default: desc
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: List of transactions with pagination
      403:
        description: Access Denied
    """
    # Security: Verify account ownership
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == account_id), None)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
    
    # Data & Filtering
    all_txns = load_table('transactions')
    account_txns = [t for t in all_txns if t['account_id'] == account_id]
    
    # Category Filter
    category = request.args.get('category')
    if category:
        account_txns = [t for t in account_txns if t.get('category') == category]

    # Search Filter
    search_term = request.args.get('search')
    if search_term:
        account_txns = [t for t in account_txns if search_term.lower() in t['description'].lower()]
    
    # Sorting
    is_asc = request.args.get('sort') == 'asc'
    account_txns.sort(key=lambda x: x['date'], reverse=not is_asc)
    
    # Pagination
    paginated_txns, meta = paginate(account_txns)
    
    return jsonify({
        "account_id": account_id,
        "meta": meta,
        "transactions": paginated_txns
    })

@accounts_bp.route('/accounts/<account_id>/cards', methods=['GET'])
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
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == account_id), None)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    all_cards = load_table('cards')
    my_cards = [c for c in all_cards if c['account_id'] == account_id]
    
    status_filter = request.args.get('status')
    if status_filter:
        my_cards = [c for c in my_cards if c['status'] == status_filter]
        
    return jsonify({
        "account_id": account_id,
        "cards": my_cards
    })

@accounts_bp.route('/transactions/<transaction_id>', methods=['GET'])
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
    transactions = load_table('transactions')
    txn = next((t for t in transactions if t['transaction_id'] == transaction_id), None)
    
    if not txn:
        abort(404)
    
    # Security: Verify ownership via account
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == txn['account_id']), None)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(txn)