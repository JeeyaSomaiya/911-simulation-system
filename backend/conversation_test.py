from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import uuid
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
CORS(app, origins=["*"])
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active sessions
active_sessions = {}

# Mock caller responses by scenario
SCENARIO_RESPONSES = {
    'house_fire': {
        'initial': "Oh my God! There's a fire! My house is on fire!",
        'location': "It's 123 Oak Street! Please hurry!",
        'details': "The fire started in the kitchen! There's smoke everywhere!"
    },
    'medical_emergency': {
        'initial': "I need an ambulance! My father is having chest pain!",
        'location': "We're at 456 Maple Drive!",
        'details': "He's 67 and has high blood pressure!"
    }
}

class MockCaller:
    def __init__(self, scenario_type):
        self.scenario_type = scenario_type
        self.emotional_state = 'PANICKED'
        self.intensity = 8
        self.turn_count = 0
        self.info_given = set()
        
    def generate_response(self, call_taker_input):
        self.turn_count += 1
        input_lower = call_taker_input.lower()
        
        # Adjust emotion based on input
        if any(word in input_lower for word in ['calm', 'help', 'okay']):
            self.intensity = max(3, self.intensity - 1)
        
        # Generate response based on question type
        if any(word in input_lower for word in ['address', 'location', 'where']):
            response = SCENARIO_RESPONSES[self.scenario_type]['location']
            self.info_given.add('location')
        elif any(word in input_lower for word in ['what', 'happening', 'emergency']):
            response = SCENARIO_RESPONSES[self.scenario_type]['details']
        else:
            responses = [
                "Please help me!",
                "What should I do?",
                "Is help coming?",
                "I'm so scared!"
            ]
            response = random.choice(responses)
        
        return response

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'AI 911 Conversation Test Server',
        'active_sessions': len(active_sessions)
    })

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    session_id = str(uuid.uuid4())
    scenario_type = data.get('scenario_type', 'house_fire')
    
    caller = MockCaller(scenario_type)
    active_sessions[session_id] = {
        'session_id': session_id,
        'caller': caller,
        'scenario_type': scenario_type,
        'conversation_history': []
    }
    
    return jsonify({
        'session_id': session_id,
        'scenario_type': scenario_type,
        'status': 'created',
        'initial_caller_message': SCENARIO_RESPONSES[scenario_type]['initial']
    })

@app.route('/api/sessions/<session_id>/message', methods=['POST'])
def send_message(session_id):
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json() or {}
    message = data.get('message', '')
    
    session = active_sessions[session_id]
    caller = session['caller']
    
    # Generate caller response
    caller_response = caller.generate_response(message)
    
    # Save to history
    turn = {
        'call_taker': message,
        'caller': caller_response,
        'emotional_state': caller.emotional_state,
        'intensity': caller.intensity
    }
    session['conversation_history'].append(turn)
    
    return jsonify({
        'caller_response': caller_response,
        'emotional_state': caller.emotional_state,
        'intensity': caller.intensity
    })

if __name__ == '__main__':
    print("AI 911 Conversation Test Server Starting...")
    print("Use POST /api/sessions to create a session")
    print("Use POST /api/sessions/{id}/message to send messages")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
