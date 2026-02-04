"""
Card Routes Module.

This module provides API endpoints for credit card management and transactions.

Endpoints:
    GET /cards/<card_id>: Get card details.
    GET /cards/<card_id>/transactions: List card transactions.
"""

from flask import Blueprint, jsonify, request, abort
from typing import Optional

from app.utils import parse_date
from app.repository import get_repository
from app.auth import check_auth
from app import limiter
from core.pagination import parse_pagination_params, create_pagination_meta


cards_bp = Blueprint('cards', __name__)


# =============================================================================
# Helper Functions
# =============================================================================

def verify_card_ownership(repo, card_id: str, current_user: dict) -> dict:
    """
    Verify that the current user owns the specified card.
    
    Checks ownership through the linked account.
    
    Args:
        repo: The repository instance.
        card_id: The card's unique identifier.
        current_user: The authenticated user dictionary.
        
    Returns:
        The card dictionary if ownership is verified.
        
    Raises:
        404: If card not found.
        403: If user doesn't own the card.
    """
    card = repo.get_card_by_id(card_id)
    
    if not card:
        abort(404, description="Card not found")
    
    # Verify ownership through the linked account
    account = repo.get_account_by_id(card['account_id'])
    
    if not account or account['user_id'] != current_user['user_id']:
        abort(403, description="Access denied")
    
    return card


def parse_amount_filter(amount_str: Optional[str]) -> Optional[float]:
    """
    Parse a minimum amount filter from query string.
    
    Args:
        amount_str: String representation of the amount.
        
    Returns:
        Float value if valid, None otherwise.
    """
    if not amount_str:
        return None
    
    try:
        return float(amount_str)
    except ValueError:
        return None


# =============================================================================
# Card Endpoints
# =============================================================================

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
        description: The card's unique identifier
    responses:
      200:
        description: Card details
        schema:
          type: object
          properties:
            card_id:
              type: string
            account_id:
              type: string
            masked_number:
              type: string
            status:
              type: string
            limit:
              type: number
            current_spend:
              type: number
            billing_day:
              type: integer
            expiry_date:
              type: string
      403:
        description: Access denied - not card owner
      404:
        description: Card not found
    """
    repo = get_repository()
    card = verify_card_ownership(repo, card_id, current_user)
    return jsonify(card)


# =============================================================================
# Card Transaction Endpoints
# =============================================================================

@cards_bp.route('/cards/<card_id>/transactions', methods=['GET'])
@check_auth
@limiter.limit("20 per minute")
def get_card_transactions(current_user, card_id):
    """
    List transactions for a specific card with filtering and pagination.
    ---
    tags:
      - Transactions
    parameters:
      - name: card_id
        in: path
        type: string
        required: true
        description: The card's unique identifier
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
        default: 1
        description: Page number
      - name: limit
        in: query
        type: integer
        default: 20
        description: Items per page
    responses:
      200:
        description: List of card transactions with pagination metadata
        schema:
          type: object
          properties:
            card_id:
              type: string
            meta:
              type: object
              properties:
                page:
                  type: integer
                limit:
                  type: integer
                has_next:
                  type: boolean
                has_prev:
                  type: boolean
            transactions:
              type: array
      403:
        description: Access denied - not card owner
      404:
        description: Card not found
    """
    repo = get_repository()
    
    # Verify ownership
    verify_card_ownership(repo, card_id, current_user)

    # Parse pagination parameters using shared utility
    params = parse_pagination_params()

    # Parse date filters (validate format)
    start_date = _parse_date_filter(request.args.get('start_date'))
    end_date = _parse_date_filter(request.args.get('end_date'))
    min_amount = parse_amount_filter(request.args.get('min_amount'))

    # Fetch filtered data
    transactions = repo.get_transactions_by_card_filtered(
        card_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        limit=params.limit,
        offset=params.offset
    )

    # Create pagination metadata
    meta = create_pagination_meta(params, len(transactions))

    return jsonify({
        "card_id": card_id,
        "meta": meta,
        "transactions": transactions
    })


def _parse_date_filter(date_str: Optional[str]) -> Optional[str]:
    """
    Validate and return a date string for filtering.
    
    Args:
        date_str: Date string in YYYY-MM-DD format.
        
    Returns:
        The date string if valid, None otherwise.
    """
    if not date_str:
        return None
    
    # Use the parse_date utility to validate
    if parse_date(date_str):
        return date_str
    
    return None
