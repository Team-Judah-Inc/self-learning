from functools import wraps
import jwt
from flask import request, jsonify, current_app
from app.utils import load_table

def check_auth(f):
    """
    Decorator to protect routes with JWT authentication.
    Verifies the Bearer token and injects the current_user into the route function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
            users = load_table('users')
            user = next((u for u in users if u['user_id'] == user_id), None)
            
            if not user:
                return jsonify({"error": "User invalid"}), 401
                
            # 4. Pass the user object to the decorated function
            return f(current_user=user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception:
            return jsonify({"error": "Authentication failed"}), 401
            
    return decorated_function