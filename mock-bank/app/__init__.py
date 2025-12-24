from flask import Flask
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config, SWAGGER_TEMPLATE

# Initialize Limiter globally so it can be imported by routes
# It will be attached to the app instance inside create_app()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)

def create_app():
    """
    Application Factory: Initializes the Flask app, 
    configs, extensions, and registers blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    Swagger(app, template=SWAGGER_TEMPLATE)
    limiter.init_app(app)

    # Register Blueprints
    # Imports are done inside the function to prevent circular dependencies
    from app.routes.users import users_bp
    from app.routes.accounts import accounts_bp
    from app.routes.cards import cards_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(cards_bp)

    return app