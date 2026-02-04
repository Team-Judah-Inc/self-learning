"""
Authentication Module.

This module provides JWT-based authentication for the Flask API.

Functions:
    check_auth: Decorator to protect routes with JWT authentication.
"""

from functools import wraps
from typing import Callable, Any

import jwt
from flask import request, jsonify, current_app

from app.repository import get_repository


def check_auth(f: Callable) -> Callable:
    """
    Decorator to protect routes with JWT authentication.
    
    Verifies the Bearer token from the Authorization header and injects
    the authenticated user into the route function as `current_user`.
    
    Args:
        f: The route function to protect.
        
    Returns:
        Decorated function that checks authentication before execution.
        
    Usage:
        @app.route('/protected')
        @check_auth
        def protected_route(current_user):
            return jsonify({"user_id": current_user['user_id']})
            
    Error Responses:
        401: Missing/invalid token, expired token, or user not found.
        
    Note:
        The decorated function must accept `current_user` as its first
        keyword argument.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get('Authorization')
        
        # 1. Check if the Authorization header is present and correctly formatted
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        
        try:
            # 2. Extract and decode the token
            token = auth_header.split(" ")[1]
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            user_id = payload['user_id']
            
            # 3. Verify that the user exists in our data
            repo = get_repository()
            user = repo.get_user_by_id(user_id)
            
            if not user:
                return jsonify({"error": "User invalid"}), 401
                
            # 4. Pass the user object to the decorated function
            return f(current_user=user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except KeyError:
            return jsonify({"error": "Invalid token payload"}), 401
        except Exception:
            return jsonify({"error": "Authentication failed"}), 401
            
    return decorated_function
