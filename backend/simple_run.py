#!/usr/bin/env python3
"""
Simple test runner for AI 911 Backend - bypasses complex dependencies
Use this for quick testing when services aren't fully set up
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Create logs directory
logs_dir = os.path.join(project_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_minimal_environment():
    """Set up minimal environment for testing"""
    
    # Set default values for testing
    test_env = {
        'FLASK_ENV': 'development',
        'SECRET_KEY': 'test-secret-key-for-development-only',
        'DATABASE_URL': 'sqlite:///test_ai_911.db',
        'REDIS_URL': 'redis://localhost:6379/0',
        'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
        'KAFKA_TOPIC_PREFIX': 'ai_911_test',
        'USE_GPU': 'false',
        'MAX_CONCURRENT_SESSIONS': '10',
        'AZURE_SPEECH_KEY': 'test_key',
        'AZURE_SPEECH_REGION': 'test_region',
        'HUGGING_FACE_TOKEN': 'test_token',
        'MODEL_PATH': './data/models',
        'CORS_ORIGINS': 'http://localhost:3000'
    }
    
    # Set environment variables if not already set
    for key, value in test_env.items():
        if not os.getenv(key):
            os.environ[key] = value
    
    logger.info("Minimal test environment configured")

def create_test_app():
    """Create a simplified Flask app for testing"""
    try:
        from flask import Flask, jsonify
        from flask_cors import CORS
        from flask_socketio import SocketIO
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
        app.config['DEBUG'] = True
        
        # Enable CORS
        CORS(app)
        
        # Initialize SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*")
        
        # Basic health check route
        @app.route('/api/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'mode': 'testing',
                'message': 'AI 911 Backend Test Server Running'
            })
        
        # Basic session route (mock)
        @app.route('/api/sessions', methods=['POST'])
        def create_session():
            import uuid
            from datetime import datetime
            
            session_id = str(uuid.uuid4())
            return jsonify({
                'session_id': session_id,
                'scenario_type': 'test_scenario',
                'status': 'created',
                'created_at': datetime.utcnow().isoformat(),
                'message': 'Test session created (limited functionality)'
            })
        
        # WebSocket test event
        @socketio.on('connect')
        def handle_connect():
            logger.info("Client connected to test server")
            socketio.emit('connected', {'status': 'Connected to test server'})
        
        return app, socketio
        
    except ImportError as e:
        logger.error(f"Missing required packages: {e}")
        logger.error("Please install: pip install flask flask-cors flask-socketio")
        return None, None

def run_full_app():
    """Try to run the full application"""
    try:
        from app import create_app, socketio
        
        config_name = os.getenv('FLASK_ENV', 'development')
        app = create_app(config_name)
        
        logger.info("Full application loaded successfully")
        return app, socketio
        
    except Exception as e:
        logger.warning(f"Could not load full application: {e}")
        logger.info("Falling back to simplified test app")
        return None, None

def main():
    """Main entry point"""
    print("AI 911 Backend - Simple Test Runner")
    print("=" * 40)
    
    # Setup minimal environment
    setup_minimal_environment()
    
    # Try to run full app first, fall back to simple app
    app, socketio = run_full_app()
    
    if app is None:
        logger.info("Creating simplified test application")
        app, socketio = create_test_app()
        
        if app is None:
            logger.error("Could not create any application")
            sys.exit(1)
    
    # Get run configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    print(f"\nStarting server on http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/api/health")
    print("Press Ctrl+C to stop\n")
    
    try:
        if socketio:
            socketio.run(app, host=host, port=port, debug=True)
        else:
            app.run(host=host, port=port, debug=True)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
