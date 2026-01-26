from flask import Blueprint, jsonify, request, current_app, abort
import jwt
import datetime
from werkzeug.security import check_password_hash
from app.utils import paginate
from app.repository import get_repository
from app.auth import check_auth

from app import limiter

users_bp = Blueprint('users', __name__)

@users_bp.route('/login', methods=['POST'])
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
              example: user1
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data: 
        return jsonify({"error": "Invalid body"}), 400

    repo = get_repository()
    user = repo.get_user_by_username(data.get('username'))
    
    if user and check_password_hash(user['password_hash'], data.get('password')):
        token = jwt.encode({
            'user_id': user['user_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            "token": token, 
            "user_id": user['user_id'],
            "expires_in": 3600
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@users_bp.route('/users/<user_id>', methods=['GET'])
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
      - name: include_settings
        in: query
        type: boolean
    responses:
      200:
        description: User details
      403:
        description: Access Denied
    """
    if current_user['user_id'] != user_id: 
        return jsonify({"error": "Access Denied"}), 403
    
    response = current_user.copy()
    del response['password_hash']
    
    if request.args.get('include_settings') != 'true': 
        response.pop('settings', None)
        
    return jsonify(response)

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
      - name: type
        in: query
        type: string
        enum: [checking, savings, credit]
      - name: currency
        in: query
        type: string
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: List of accounts
    """
    if current_user['user_id'] != user_id: 
        return jsonify({"error": "Access Denied"}), 403
    
    repo = get_repository()
    
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
    accounts = repo.get_accounts_by_user_filtered(
        user_id,
        type=request.args.get('type'),
        currency=request.args.get('currency'),
        limit=limit,
        offset=offset
    )
    
    meta = {
        "page": page,
        "limit": limit,
        "has_next": len(accounts) == limit,
        "has_prev": page > 1
    }
        
    return jsonify({"meta": meta, "accounts": accounts})