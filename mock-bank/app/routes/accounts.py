"""
Account Routes Module.

This module provides API endpoints for account management and transactions.

Endpoints:
    GET /accounts/<account_id>: Get account details.
    GET /accounts/<account_id>/transactions: List account transactions.
    GET /accounts/<account_id>/cards: List cards linked to account.
    GET /transactions/<transaction_id>: Get transaction receipt.
"""

from flask import Blueprint, jsonify, request, abort

from app.repository import get_repository
from app.auth import check_auth
from app import limiter
from core.pagination import parse_pagination_params, create_pagination_meta


accounts_bp = Blueprint('accounts', __name__)


# =============================================================================
# Helper Functions
# =============================================================================

def verify_account_ownership(repo, account_id: str, current_user: dict) -> dict:
    """
    Verify that the current user owns the specified account.
    
    Args:
        repo: The repository instance.
        account_id: The account's unique identifier.
        current_user: The authenticated user dictionary.
        
    Returns:
        The account dictionary if ownership is verified.
        
    Raises:
        404: If account not found.
        403: If user doesn't own the account.
    """
    account = repo.get_account_by_id(account_id)
    
    if not account:
        abort(404, description="Account not found")
    
    if account['user_id'] != current_user['user_id']:
        abort(403, description="Access denied")
    
    return account


# =============================================================================
# Account Endpoints
# =============================================================================

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
        description: The account's unique identifier
    responses:
      200:
        description: Account details
        schema:
          type: object
          properties:
            account_id:
              type: string
            user_id:
              type: string
            type:
              type: string
            currency:
              type: string
            balance:
              type: number
            status:
              type: string
      403:
        description: Access denied - not account owner
      404:
        description: Account not found
    """
    repo = get_repository()
    account = verify_account_ownership(repo, account_id, current_user)
    return jsonify(account)


# =============================================================================
# Transaction Endpoints
# =============================================================================

@accounts_bp.route('/accounts/<account_id>/transactions', methods=['GET'])
@check_auth
@limiter.limit("20 per minute")
def get_account_transactions(current_user, account_id):
    """
    List transactions for an account with filtering and pagination.
    ---
    tags:
      - Transactions
    parameters:
      - name: account_id
        in: path
        type: string
        required: true
        description: The account's unique identifier
      - name: category
        in: query
        type: string
        description: Filter by transaction category
      - name: search
        in: query
        type: string
        description: Search in transaction descriptions
      - name: sort
        in: query
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort order by date
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: limit
        in: query
        type: integer
        default: 20
        description: Items per page
    responses:
      200:
        description: List of transactions with pagination metadata
        schema:
          type: object
          properties:
            account_id:
              type: string
            meta:
              type: object
            transactions:
              type: array
      403:
        description: Access denied - not account owner
      404:
        description: Account not found
    """
    repo = get_repository()
    
    # Verify ownership
    verify_account_ownership(repo, account_id, current_user)
    
    # Parse pagination parameters using shared utility
    params = parse_pagination_params()

    # Fetch filtered data
    transactions = repo.get_transactions_by_account_filtered(
        account_id,
        category=request.args.get('category'),
        search=request.args.get('search'),
        sort=request.args.get('sort', 'desc'),
        limit=params.limit,
        offset=params.offset
    )
    
    # Create pagination metadata
    meta = create_pagination_meta(params, len(transactions))
    
    return jsonify({
        "account_id": account_id,
        "meta": meta,
        "transactions": transactions
    })


# =============================================================================
# Card Endpoints
# =============================================================================

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
        description: The account's unique identifier
      - name: status
        in: query
        type: string
        enum: [ACTIVE, BLOCKED, EXPIRED]
        description: Filter by card status
    responses:
      200:
        description: List of cards
        schema:
          type: object
          properties:
            account_id:
              type: string
            cards:
              type: array
      403:
        description: Access denied - not account owner
      404:
        description: Account not found
    """
    repo = get_repository()
    
    # Verify ownership
    verify_account_ownership(repo, account_id, current_user)
    
    # Fetch cards
    cards = repo.get_cards_by_account(account_id)
    
    # Apply status filter if provided
    status_filter = request.args.get('status')
    if status_filter:
        cards = [c for c in cards if c['status'] == status_filter]
        
    return jsonify({
        "account_id": account_id,
        "cards": cards
    })


# =============================================================================
# Transaction Receipt Endpoint
# =============================================================================

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
        description: The transaction's unique identifier
    responses:
      200:
        description: Transaction details
        schema:
          type: object
          properties:
            transaction_id:
              type: string
            account_id:
              type: string
            amount:
              type: number
            date:
              type: string
            description:
              type: string
            category:
              type: string
            type:
              type: string
      403:
        description: Access denied - not transaction owner
      404:
        description: Transaction not found
    """
    repo = get_repository()
    txn = repo.get_transaction_by_id(transaction_id)
    
    if not txn:
        abort(404, description="Transaction not found")
    
    # Determine the account ID (handle both account and card transactions)
    account_id = _get_transaction_account_id(repo, txn)
    
    if not account_id:
        return jsonify({"error": "Transaction orphan"}), 404

    # Verify ownership through the account
    verify_account_ownership(repo, account_id, current_user)
        
    return jsonify(txn)


def _get_transaction_account_id(repo, txn: dict) -> str:
    """
    Get the account ID associated with a transaction.
    
    For account transactions, returns the account_id directly.
    For card transactions, looks up the card to find the linked account.
    
    Args:
        repo: The repository instance.
        txn: The transaction dictionary.
        
    Returns:
        The account ID, or None if not found.
    """
    # Direct account transaction
    if txn.get('account_id'):
        return txn['account_id']
    
    # Card transaction - look up the card
    if txn.get('card_id'):
        card = repo.get_card_by_id(txn['card_id'])
        if card:
            return card['account_id']
    
    return None
