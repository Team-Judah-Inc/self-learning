from flask import Blueprint, jsonify, request, current_app, abort
from app.utils import paginate
from app.repository import get_repository
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
    repo = get_repository()
    account = repo.get_account_by_id(account_id)
    
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
    repo = get_repository()
    account = repo.get_account_by_id(account_id)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
    
    # Pagination Params
    try:
        limit = int(request.args.get('limit', current_app.config['DEFAULT_PAGE_SIZE']))
        page = int(request.args.get('page', 1))
    except ValueError:
        limit = current_app.config['DEFAULT_PAGE_SIZE']
        page = 1
        
    max_limit = current_app.config['MAX_PAGE_SIZE']
    limit = max(1, min(limit, max_limit))
    page = max(1, page)
    offset = (page - 1) * limit

    # Fetch Filtered Data
    transactions = repo.get_transactions_by_account_filtered(
        account_id,
        category=request.args.get('category'),
        search=request.args.get('search'),
        sort=request.args.get('sort', 'desc'),
        limit=limit,
        offset=offset
    )
    
    # Note: Total count for metadata would require a separate COUNT query.
    # For now, we simplify metadata or would need to add a count method to repo.
    # Let's provide basic meta based on current page.
    
    meta = {
        "page": page,
        "limit": limit,
        "has_next": len(transactions) == limit, # Approximate check
        "has_prev": page > 1
    }
    
    return jsonify({
        "account_id": account_id,
        "meta": meta,
        "transactions": transactions
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
    repo = get_repository()
    account = repo.get_account_by_id(account_id)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    my_cards = repo.get_cards_by_account(account_id)
    
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
    repo = get_repository()
    txn = repo.get_transaction_by_id(transaction_id)
    
    if not txn:
        abort(404)
    
    # Security: Verify ownership via account
    # Note: Card transactions might need card lookup first, but for now assuming account_id is present or linked
    # If txn is card txn, it has card_id. We need to find account from card.
    
    account_id = txn.get('account_id')
    if not account_id and txn.get('card_id'):
        card = repo.get_card_by_id(txn['card_id'])
        if card: account_id = card['account_id']

    if not account_id:
         return jsonify({"error": "Transaction orphan"}), 404

    account = repo.get_account_by_id(account_id)
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(txn)