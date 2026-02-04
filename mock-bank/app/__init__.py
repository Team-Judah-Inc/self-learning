"""
Flask Application Package.

This package contains the Flask API application for the mock banking system.

Modules:
    auth: JWT authentication decorator.
    repository: Data access layer for the API.
    utils: Utility functions for the API.
    routes/: API endpoint blueprints.

Functions:
    create_app: Application factory for creating Flask instances.
"""

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


def create_app() -> Flask:
    """
    Application Factory: Create and configure a Flask application instance.
    
    This factory pattern allows for:
    - Multiple app instances with different configurations (testing, production)
    - Delayed initialization of extensions
    - Clean separation of concerns
    
    Returns:
        Configured Flask application instance.
        
    Example:
        >>> app = create_app()
        >>> app.run(host='0.0.0.0', port=5000)
        
    Configuration:
        The app is configured from the Config class in config.py.
        Key settings include:
        - DB_TYPE: Database backend ('sqlite' or 'json')
        - SQLALCHEMY_DATABASE_URI: Database connection string
        - SECRET_KEY: JWT signing key
        - DEFAULT_PAGE_SIZE: Default pagination limit
        - MAX_PAGE_SIZE: Maximum pagination limit
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    _init_extensions(app)
    
    # Register Blueprints
    _register_blueprints(app)

    return app


def _init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions.
    
    Args:
        app: The Flask application instance.
    """
    Swagger(app, template=SWAGGER_TEMPLATE)
    limiter.init_app(app)


def _register_blueprints(app: Flask) -> None:
    """
    Register API blueprints with the application.
    
    Imports are done inside the function to prevent circular dependencies.
    
    Args:
        app: The Flask application instance.
    """
    from app.routes.users import users_bp
    from app.routes.accounts import accounts_bp
    from app.routes.cards import cards_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(cards_bp)
