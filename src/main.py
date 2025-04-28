"""
Scout-Edge - Application for tracking current trends in the AI field.
"""
import os
import logging
from dotenv import load_dotenv

# Import configuration settings
import config

# Database initialization
from db.vector_store import init_vector_store

# Log configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scout_edge.log")
    ]
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Prepare the working environment."""
    load_dotenv()
    
    # Check API keys
    missing_keys = []
    if not config.OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
    if not config.GITHUB_API_KEY:
        missing_keys.append("GITHUB_API_KEY")
    
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
        logger.warning("Please define the missing keys in the .env file.")
    
    # Create vector storage directory
    os.makedirs(os.path.dirname(config.VECTORSTORE_PATH), exist_ok=True)


def main():
    """Main application startup function."""
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}...")
    
    # Prepare the working environment
    setup_environment()
    
    # Initialize vector store
    try:
        # We'll use this later when implementing agents
        _ = init_vector_store()
        logger.info("Vector store successfully initialized.")
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        return
    
    # Code for initializing agents and tools will be added here
    
    logger.info(f"{config.APP_NAME} successfully started.")
    
    # Simple CLI output for now
    app_desc = config.APP_DESCRIPTION
    print(f"\n{config.APP_NAME} - {app_desc}\n")
    print("This application is still in development.")
    print("More features will be added in future versions.")


if __name__ == "__main__":
    main()
