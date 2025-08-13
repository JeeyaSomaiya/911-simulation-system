#!/usr/bin/env python3
"""
AI 911 Emergency Call Simulation Backend - Application Entry Point
This file serves as the main entry point for the Flask application
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_dir, 'logs', 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = os.path.join(project_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.info(f"Created logs directory: {logs_dir}")

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly")
    
    # Optional but recommended variables
    optional_vars = [
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION',
        'HUGGING_FACE_TOKEN'
    ]
    
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        logger.info(f"Optional environment variables not set: {', '.join(missing_optional)}")
        logger.info("AI features will be limited without these credentials")

def main():
    """Main application entry point"""
    try:
        # Create necessary directories
        create_logs_directory()
        
        # Validate environment
        validate_environment()
        
        # Import and create Flask app
        from app import create_app, socketio
        
        # Get configuration from environment
        config_name = os.getenv('FLASK_ENV', 'development')
        
        logger.info(f"Starting AI 911 Backend in {config_name} mode")
        
        # Create Flask application
        app = create_app(config_name)
        
        # Get configuration
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = config_name == 'development'
        
        logger.info(f"Application will run on http://{host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the application with SocketIO
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            log_output=True
        )
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please ensure all dependencies are installed")
        logger.error("Run: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
