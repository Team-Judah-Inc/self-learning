import os

class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET", "dev_secret_key")
    DATA_DIR = 'mock_data'
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 20

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Banking API",
        "description": "A mock banking API with JWT Authentication and Rate Limiting",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter your bearer token in the format **Bearer <token>**"
        }
    },
    "security": [{"Bearer": []}]
}