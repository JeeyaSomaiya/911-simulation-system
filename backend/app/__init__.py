from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.config import config
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

socketio = SocketIO()

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)
    
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    CORS(app, origins=['*'])
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register basic routes
    @app.route('/api/health')
    def health_check():
        return {
            'status': 'healthy',
            'services': {
                'database': 'connected',
                'redis': 'simulated',
                'event_bus': 'simulated'
            },
            'message': 'AI 911 Backend running in basic mode'
        }
    
    @app.route('/api/sessions', methods=['POST'])
    def create_session():
        import uuid
        from datetime import datetime
        from flask import request
        
        data = request.get_json() or {}
        session_id = str(uuid.uuid4())
        
        return {
            'session_id': session_id,
            'trainee_id': data.get('trainee_id'),
            'scenario_type': data.get('scenario_type'),
            'status': 'created',
            'created_at': datetime.utcnow().isoformat(),
            'caller_profile': 'simulated_caller',
            'initial_emotional_state': 'WORRIED'
        }
    
    app.logger.info(f"Flask app created successfully")
    return app
