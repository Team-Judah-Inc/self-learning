import logging
from app import create_app

# Configure logging for the API server
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the application instance
app = create_app()

if __name__ == "__main__":
    logger.info("🚀 Starting API Server...")
    logger.info("📄 Swagger UI available at: http://localhost:5000/apidocs")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start API server: {e}")
