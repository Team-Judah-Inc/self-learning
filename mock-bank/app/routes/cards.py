from flask import Blueprint, jsonify, request, current_app, abort
from app.utils import paginate, parse_date
from app.repository import get_repository
from app.auth import check_auth
from app import limiter

# Define the Blueprint for card-related routes
cards_bp = Blueprint('cards', __name__)

@cards_bp.route('/cards/<card_id>', methods=['GET'])
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
    repo = get_repository()
    card = repo.get_card_by_id(card_id)
    
    if not card:
        abort(404)
        
    # Ownership check: Find the account linked to the card and verify user_id
    account = repo.get_account_by_id(card['account_id'])
    
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify(card)

@cards_bp.route('/cards/<card_id>/transactions', methods=['GET'])
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
        description: Filter by start date (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        format: date
        description: Filter by end date (YYYY-MM-DD)
      - name: min_amount
        in: query
        type: number
        description: Filter by minimum absolute amount
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: List of card transactions
      403:
        description: Access Denied
    """
    # Authorization: Ensure the card belongs to the user
    repo = get_repository()
    card = repo.get_card_by_id(card_id)
    if not card:
        abort(404)
        
    account = repo.get_account_by_id(card['account_id'])
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

    # Parse Filters
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    min_amount_str = request.args.get('min_amount')
    
    min_amount = None
    if min_amount_str:
        try: min_amount = float(min_amount_str)
        except ValueError: pass

    # Fetch Filtered Data
    transactions = repo.get_transactions_by_card_filtered(
        card_id,
        start_date=start_str if start_str and parse_date(start_str) else None,
        end_date=end_str if end_str and parse_date(end_str) else None,
        min_amount=min_amount,
        limit=limit,
        offset=offset
    )

    meta = {
        "page": page,
        "limit": limit,
        "has_next": len(transactions) == limit,
        "has_prev": page > 1
    }

    return jsonify({
        "card_id": card_id,
        "meta": meta,
        "transactions": transactions
    })