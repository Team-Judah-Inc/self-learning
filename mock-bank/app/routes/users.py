"""
User Routes Module.

This module provides API endpoints for user authentication and profile management.

Endpoints:
    POST /login: Authenticate and receive a JWT token.
    GET /users/<user_id>: Get user profile.
    GET /users/<user_id>/accounts: List user's accounts.
"""

from flask import Blueprint, jsonify, request, current_app
import jwt
import datetime
from werkzeug.security import check_password_hash

from app.repository import get_repository
from app.auth import check_auth
from app import limiter
from core.pagination import parse_pagination_params, create_pagination_meta


users_bp = Blueprint('users', __name__)


# =============================================================================
# Authentication Endpoints
# =============================================================================

@users_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate user and return JWT token.
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
              example: user1
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful, returns JWT token
        schema:
          type: object
          properties:
            token:
              type: string
            user_id:
              type: string
            expires_in:
              type: integer
      400:
        description: Invalid request body
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid body"}), 400

    repo = get_repository()
    user = repo.get_user_by_username(data.get('username'))
    
    if user and check_password_hash(user['password_hash'], data.get('password')):
        token = jwt.encode(
            {
                'user_id': user['user_id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            current_app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            "token": token,
            "user_id": user['user_id'],
            "expires_in": 3600
        })
    
    return jsonify({"error": "Invalid credentials"}), 401


# =============================================================================
# User Profile Endpoints
# =============================================================================

@users_bp.route('/users/<user_id>', methods=['GET'])
@check_auth
def get_user(current_user, user_id):
    """
    Get user profile.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: The user's unique identifier
      - name: include_settings
        in: query
        type: boolean
        description: Include user settings in response
    responses:
      200:
        description: User profile details
        schema:
          type: object
          properties:
            user_id:
              type: string
            username:
              type: string
            first_name:
              type: string
            last_name:
              type: string
            email:
              type: string
            city:
              type: string
      403:
        description: Access denied - can only view own profile
    """
    # Security: Users can only view their own profile
    if current_user['user_id'] != user_id:
        return jsonify({"error": "Access Denied"}), 403
    
    # Build response (exclude sensitive data)
    response = current_user.copy()
    del response['password_hash']
    
    # Optionally exclude settings
    if request.args.get('include_settings') != 'true':
        response.pop('settings', None)
        
    return jsonify(response)


# =============================================================================
# User Accounts Endpoints
# =============================================================================

@users_bp.route('/users/<user_id>/accounts', methods=['GET'])
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
        description: The user's unique identifier
      - name: type
        in: query
        type: string
        enum: [CHECKING, SAVINGS]
        description: Filter by account type
      - name: currency
        in: query
        type: string
        description: Filter by currency code
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
        description: List of accounts with pagination metadata
        schema:
          type: object
          properties:
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
            accounts:
              type: array
              items:
                type: object
      403:
        description: Access denied - can only view own accounts
    """
    # Security: Users can only view their own accounts
    if current_user['user_id'] != user_id:
        return jsonify({"error": "Access Denied"}), 403
    
    repo = get_repository()
    
    # Parse pagination parameters using shared utility
    params = parse_pagination_params()

    # Fetch filtered data
    accounts = repo.get_accounts_by_user_filtered(
        user_id,
        type=request.args.get('type'),
        currency=request.args.get('currency'),
        limit=params.limit,
        offset=params.offset
    )
    
    # Create pagination metadata
    meta = create_pagination_meta(params, len(accounts))
        
    return jsonify({
        "meta": meta,
        "accounts": accounts
    })
