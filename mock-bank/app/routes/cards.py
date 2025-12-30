from flask import Blueprint, jsonify, request, current_app, abort
from app.utils import load_table, paginate, parse_date
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
    cards = load_table('cards')
    card = next((c for c in cards if c['card_id'] == card_id), None)
    
    if not card:
        abort(404)
    
    # Ownership check: Find the account linked to the card and verify user_id
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == card['account_id']), None)
    
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
    cards = load_table('cards')
    card = next((c for c in cards if c['card_id'] == card_id), None)
    if not card:
        abort(404)
        
    accounts = load_table('accounts')
    account = next((a for a in accounts if a['account_id'] == card['account_id']), None)
    if not account or account['user_id'] != current_user['user_id']:
        return jsonify({"error": "Access Denied"}), 403

    # Load and filter transactions
    all_transactions = load_table('transactions')
    card_txns = [t for t in all_transactions if t.get('card_id') == card_id]

    # Date Filters
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    
    if start_str and parse_date(start_str):
        card_txns = [t for t in card_txns if parse_date(t['date']) >= parse_date(start_str)]
    if end_str and parse_date(end_str):
        card_txns = [t for t in card_txns if parse_date(t['date']) <= parse_date(end_str)]

    # Amount Filter
    min_amount = request.args.get('min_amount')
    if min_amount:
        try:
            limit_val = float(min_amount)
            card_txns = [t for t in card_txns if abs(t['amount']) >= limit_val]
        except ValueError:
            pass

    # Pagination
    results, meta = paginate(card_txns)

    return jsonify({
        "card_id": card_id,
        "meta": meta,
        "transactions": results
    })