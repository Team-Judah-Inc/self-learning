from flask import Blueprint, jsonify, request, current_app, abort
import jwt
import datetime
from werkzeug.security import check_password_hash
from app.utils import load_table, paginate
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

    users = load_table('users')
    user = next((u for u in users if u['username'] == data.get('username')), None)
    
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