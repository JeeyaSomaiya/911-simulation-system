import os
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
import redis

from ai_generator import HuggingFaceCallerGenerator
from session_manager import SessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Connected to Redis")
except:
    logger.warning("Redis not available - using in-memory session storage")
    redis_client = None

generator = HuggingFaceCallerGenerator()
session_manager = SessionManager()

@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        trainee_id = data.get('trainee_id', 'default')
        scenario_type = data.get('scenario_type', '10-01')
        
        session = session_manager.create_session(trainee_id, scenario_type)
        
        logger.info(f"Created session {session.session_id} for {scenario_type}")
        
        return jsonify({
            'session_id': session.session_id,
            'scenario_type': session.scenario_type.value,
            'status': 'created'
        })
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session.session_id,
            'scenario_type': session.scenario_type.value,
            'emotional_state': session.caller_state.emotional_state.value,
            'intensity': session.caller_state.intensity,
            'scenario_progress': session.caller_state.scenario_progress,
            'is_active': session.is_active,
            'key_details_revealed': session.caller_state.key_details_revealed
        })
    
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id):
    try:
        session_manager.terminate_session(session_id)
        logger.info(f"Terminated session {session_id}")
        return jsonify({'status': 'terminated'})
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<session_id>/message', methods=['POST'])
def send_message(session_id):
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        caller_response, updated_state = generator.generate_response(
            session.caller_state, message
        )
        
        session_manager.update_session(session_id, updated_state)
        
        logger.info(f"Message exchange in {session_id}: {message[:30]}... -> {caller_response[:30]}...")
        
        return jsonify({
            'caller_response': caller_response,
            'emotional_state': updated_state.emotional_state.value,
            'intensity': updated_state.intensity,
            'scenario_progress': updated_state.scenario_progress,
            'key_details_revealed': updated_state.key_details_revealed,
            'conversation_history': updated_state.conversation_history[-4:]
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    from session_manager import sessions
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': generator.model is not None,
        'model_path': generator.model_path,
        'active_sessions': len([s for s in sessions.values() if s.is_active])
    })

if __name__ == '__main__':
    logger.info("Starting 911 Call Simulation Server")
    logger.info(f"Using Llama-3.1-8B from: {generator.model_path}")
    logger.info("Press Ctrl+C to stop")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
    