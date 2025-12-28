import os

class Config:
    # Point this to where your generate_data.py writes files
    DATA_DIR = os.environ.get('DATA_DIR', 'mock_data')
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_123')
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

# Swagger UI Settings
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Banking API V4.0",
        "description": "Modular Banking API using Flask Blueprints",
        "version": "4.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Format: **Bearer &lt;token&gt;**"
        }
    },
    "security": [
        {"Bearer": []}
    ]
}