#!/usr/bin/env python3

import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import torch
from threading import Lock

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import redis
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import BitsAndBytesConfig
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, origins=["http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode='threading')

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

class EmotionalState(Enum):
    CALM = "calm"
    WORRIED = "worried"
    PANICKED = "panicked"
    HYSTERICAL = "hysterical"
    RELIEVED = "relieved"

class ScenarioType(Enum):
    MEDICAL_EMERGENCY = "medical_emergency"
    HOUSE_FIRE = "house_fire"
    TRAFFIC_ACCIDENT = "traffic_accident"
    TRAFFIC_ACCIDENT_10_01 = "10-01"  # Injury Motor Vehicle Collision
    ROBBERY = "robbery"
    ALARM = "alarm"

@dataclass
class CallerState:
    emotional_state: EmotionalState
    intensity: int
    scenario_type: ScenarioType
    key_details_revealed: List[str]
    conversation_history: List[Dict[str, str]]
    caller_profile: Dict[str, Any]
    scenario_progress: float

@dataclass
class SessionData:
    session_id: str
    trainee_id: str
    scenario_type: ScenarioType
    caller_state: CallerState
    created_at: datetime
    last_activity: datetime
    is_active: bool

class Llama3CallerGenerator:
    def __init__(self):
        # Use the local path to your model
        self.model_path = "/home/ubuntu/.llama/checkpoints/Llama3.3-70B-Instruct-hf"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.scenario_contexts = self._load_scenario_contexts()
        self.lock = Lock()  # For thread-safe model access
        self.load_model()
        logger.info("Llama-3 Caller Generator initialized")
    
    def _load_scenario_contexts(self):
        return {
            ScenarioType.HOUSE_FIRE: {
                "location": "65 Eldorado Close Northeast, Calgary",
                "caller_name": "Sarah Johnson",
                "phone": "403-555-0123",
                "situation": "Kitchen fire started from overheated oil while cooking dinner. Fire spread rapidly through kitchen and is now reaching the living room. Smoke alarms are blaring.",
                "current_status": "All family members (Sarah, husband Mike, two children ages 8 and 12) evacuated safely and are standing across the street. House is actively burning.",
                "caller_background": "35-year-old mother, teacher, lives in suburban Calgary. Generally calm under pressure but terrified about losing home. Protective of family.",
            },
            ScenarioType.MEDICAL_EMERGENCY: {
                "location": "123 Main Street, Calgary", 
                "caller_name": "Linda Smith",
                "phone": "403-555-0456",
                "situation": "Neighbor Bob Miller (67 years old) collapsed suddenly while walking his dog. He appears unconscious and unresponsive.",
                "current_status": "Bob is lying on the sidewalk, breathing but unconscious. His dog is sitting nearby. Linda is kneeling beside him.",
                "caller_background": "42-year-old nurse, lives next door to Bob. Knows basic first aid but is concerned about his condition.",
            },
            ScenarioType.ROBBERY: {
                "location": "68 Eldorado Close Northeast, Calgary",
                "caller_name": "Mike Wilson", 
                "phone": "403-555-0789",
                "situation": "Witnessed armed robbery at neighbor's house. Heard gunshots and saw masked man break into house across the street.",
                "current_status": "Suspect still in house, may be armed. Mike is hiding in his own house watching from upstairs window.",
                "caller_background": "28-year-old construction worker, lives alone. Never experienced anything like this before. Very shaken.",
            },
            ScenarioType.TRAFFIC_ACCIDENT: {
                "location": "16th Avenue and Centre Street, Calgary",
                "caller_name": "Jennifer Brown",
                "phone": "403-555-0321",
                "situation": "Two-car collision at busy intersection. Both vehicles appear to have significant damage and people are injured.",
                "current_status": "Both drivers are conscious but appear hurt. Traffic is backing up. Jennifer pulled over to help.",
                "caller_background": "29-year-old accountant, drives this route daily. Wants to help but staying safe.",
            },
            ScenarioType.TRAFFIC_ACCIDENT_10_01: {
                "location": "Cranston Ave SE / Deerfoot Tr SE",
                "caller_name": "Broderick Greene", 
                "phone": "403-561-9988",
                "situation": "Witnessed a rollover accident. White SUV (possibly VW or BMW with circle logo) is currently in the ditch off southbound Deerfoot Trail just south of Cranston Ave SE. Vehicle appears to have rolled over due to black ice conditions.",
                "current_status": "Drive-by caller who has already left the scene. Observed the accident about 1 minute ago. Driver appears to be injured and trapped in the overturned vehicle.",
                "caller_background": "Excited drive-by caller who witnessed the accident while driving. Not at scene anymore but concerned about the driver's safety.",
            },
            ScenarioType.ALARM: {
                "location": "456 Bank Street, Calgary",
                "caller_name": "Tom Henderson",
                "phone": "403-555-0654",
                "situation": "Security alarm triggered at TD Bank branch. Motion detected inside building after hours.",
                "current_status": "Monitoring from central security station. Cameras show possible intruder movement inside bank.",
                "caller_background": "45-year-old security guard, 15 years experience. Professional and calm but alert.",
            }
        }
    
    def load_model(self):
        try:
            logger.info(f"Loading Llama-3 model from: {self.model_path}")
            
            # Configure 4-bit quantization
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
            
            # Load tokenizer and model from local path
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2"
            )
            
            logger.info("Llama-3 model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error("Please ensure the model files are in the correct location")
            logger.error(f"Model path: {self.model_path}")
            raise RuntimeError("Model failed to load - please check model path and resources")

    def generate_response(self, caller_state: CallerState, call_taker_message: str) -> Tuple[str, CallerState]:
        """Generate response using Llama-3"""
        context = self.scenario_contexts.get(caller_state.scenario_type)
        if not context:
            logger.error(f"No context for scenario: {caller_state.scenario_type}")
            return "I need help!", caller_state
        
        try:
            # Build messages for Llama-3 chat format
            messages = self._build_messages(caller_state, call_taker_message, context)
            
            # Generate with model
            with self.lock:
                inputs = self.tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    return_tensors="pt"
                ).to(self.model.device)
                
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                response = self.tokenizer.decode(
                    outputs[0][len(inputs[0]):], 
                    skip_special_tokens=True
                )
            
            # Clean response
            response = self._clean_response(response)
            
            # Update state
            new_state = self._update_state(caller_state, call_taker_message, response)
            
            return response, new_state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I need help!", caller_state
    
    def _build_messages(self, caller_state: CallerState, call_taker_message: str, context: dict) -> list:
        """Build messages in Llama-3 chat format"""
        system_prompt = self._create_system_prompt(caller_state, context)
        
        # Start with system message
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for exchange in caller_state.conversation_history[-6:]:  # Last 6 exchanges
            role = "user" if exchange['role'] == 'call_taker' else "assistant"
            messages.append({"role": role, "content": exchange['content']})
        
        # Add current call taker message
        messages.append({"role": "user", "content": call_taker_message})
        
        return messages
    
    def _create_system_prompt(self, caller_state: CallerState, context: dict) -> str:
        """Create system prompt defining the scenario and role"""
        return f"""You are {context['caller_name']}, calling 911 in a real emergency. Respond as this person in this exact situation.

### EMERGENCY DETAILS ###
Location: {context['location']}
Your phone: {context['phone']}
What happened: {context['situation']}
Current status: {context['current_status']}

### YOUR BACKGROUND ###
{context['caller_background']}

### YOUR CURRENT STATE ###
Emotional state: {caller_state.emotional_state.value} (intensity: {caller_state.intensity}/10)
Call progress: {caller_state.scenario_progress:.0%}

### INSTRUCTIONS ###
1. You are a REAL PERSON in a REAL EMERGENCY
2. Respond directly and naturally to the 911 operator
3. Answer questions clearly but don't volunteer unnecessary details
4. Show emotions appropriate to your stress level
5. Keep responses concise (1-3 sentences)
6. Never break character or mention you're an AI
7. Focus on critical information for emergency responders"""

    def _clean_response(self, response: str) -> str:
        """Clean up generated response"""
        # Remove any role prefixes
        for prefix in ["<|im_end|>", "<|im_start|>", "assistant", "911 caller:"]:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Remove trailing incomplete sentences
        if response and response[-1] not in ['.', '!', '?']:
            if '.' in response:
                response = response.rsplit('.', 1)[0] + '.'
            elif '!' in response:
                response = response.rsplit('!', 1)[0] + '!'
        
        # Ensure minimum response length
        if len(response.split()) < 3:
            return "Please help me!"
        
        return response.strip()
    
    def _update_state(self, caller_state: CallerState, call_taker_message: str, response: str) -> CallerState:
        """Update caller state based on conversation"""
        new_state = CallerState(
            emotional_state=caller_state.emotional_state,
            intensity=caller_state.intensity,
            scenario_type=caller_state.scenario_type,
            key_details_revealed=caller_state.key_details_revealed.copy(),
            conversation_history=caller_state.conversation_history.copy(),
            caller_profile=caller_state.caller_profile.copy(),
            scenario_progress=caller_state.scenario_progress
        )
        
        # Add to conversation history
        new_state.conversation_history.append({
            'role': 'call_taker', 
            'content': call_taker_message,
            'timestamp': datetime.now().isoformat()
        })
        new_state.conversation_history.append({
            'role': 'caller', 
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update revealed details
        revealed_details = {
            'location': ['where', 'location', 'address'],
            'situation': ['happened', 'wrong', 'emergency'],
            'people': ['anyone', 'people', 'others'],
            'medical': ['hurt', 'injured', 'medical'],
            'contact': ['phone', 'number', 'contact']
        }
        
        for detail, keywords in revealed_details.items():
            if any(kw in call_taker_message.lower() for kw in keywords):
                if detail not in new_state.key_details_revealed:
                    new_state.key_details_revealed.append(detail)
                    new_state.scenario_progress = min(1.0, new_state.scenario_progress + 0.15)
        
        # Update emotional state
        if "calm down" in call_taker_message.lower() and new_state.intensity > 5:
            new_state.intensity -= 1
        elif "help is coming" in call_taker_message.lower():
            new_state.intensity = max(3, new_state.intensity - 2)
        elif new_state.scenario_progress < 0.5:
            new_state.intensity = min(10, new_state.intensity + 0.5)
        
        # Update emotional state based on intensity
        if new_state.intensity <= 3:
            new_state.emotional_state = EmotionalState.RELIEVED
        elif new_state.intensity <= 5:
            new_state.emotional_state = EmotionalState.WORRIED
        elif new_state.intensity <= 8:
            new_state.emotional_state = EmotionalState.PANICKED
        else:
            new_state.emotional_state = EmotionalState.HYSTERICAL
        
        return new_state

    def generate_initial_response(self, scenario_type: ScenarioType) -> str:
        """Generate initial emergency call opening"""
        context = self.scenario_contexts.get(scenario_type)
        if not context:
            return "Help! There's an emergency!"
        
        try:
            messages = [
                {"role": "system", "content": "You're calling 911 in an emergency. State the problem concisely in 1-2 sentences."},
                {"role": "user", "content": f"EMERGENCY: {context['situation']} at {context['location']}"}
            ]
            
            with self.lock:
                inputs = self.tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    return_tensors="pt"
                ).to(self.model.device)
                
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=100,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95
                )
                
                response = self.tokenizer.decode(
                    outputs[0][len(inputs[0]):], 
                    skip_special_tokens=True
                )
            
            return self._clean_response(response)
            
        except Exception as e:
            logger.error(f"Error generating initial response: {e}")
            return "Help! There's an emergency!"

# Initialize the generator
generator = Llama3CallerGenerator()

# Session management
sessions = {}

class SessionManager:
    def create_session(self, trainee_id: str, scenario_type: str) -> SessionData:
        session_id = str(uuid.uuid4())
        scenario_map = {
            "medical_emergency": ScenarioType.MEDICAL_EMERGENCY,
            "house_fire": ScenarioType.HOUSE_FIRE,
            "traffic_accident": ScenarioType.TRAFFIC_ACCIDENT,
            "10-01": ScenarioType.TRAFFIC_ACCIDENT_10_01,
            "robbery": ScenarioType.ROBBERY,
            "alarm": ScenarioType.ALARM
        }
        
        scenario_enum = scenario_map.get(scenario_type, ScenarioType.HOUSE_FIRE)
        
        # Set initial state
        initial_state = CallerState(
            emotional_state=EmotionalState.PANICKED,
            intensity=8,
            scenario_type=scenario_enum,
            key_details_revealed=[],
            conversation_history=[],
            caller_profile={},
            scenario_progress=0.0
        )
        
        session = SessionData(
            session_id=session_id,
            trainee_id=trainee_id,
            scenario_type=scenario_enum,
            caller_state=initial_state,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            is_active=True
        )
        
        sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        return sessions.get(session_id)
    
    def update_session(self, session_id: str, caller_state: CallerState):
        if session_id in sessions:
            sessions[session_id].caller_state = caller_state
            sessions[session_id].last_activity = datetime.now()
    
    def terminate_session(self, session_id: str):
        if session_id in sessions:
            sessions[session_id].is_active = False

session_manager = SessionManager()

# API Routes
@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        trainee_id = data.get('trainee_id', 'default')
        scenario_type = data.get('scenario_type', 'house_fire')
        
        session = session_manager.create_session(trainee_id, scenario_type)
        initial_message = generator.generate_initial_response(session.scenario_type)
        
        logger.info(f"Created session {session.session_id} for {scenario_type}")
        
        return jsonify({
            'session_id': session.session_id,
            'scenario_type': session.scenario_type.value,
            'status': 'created',
            'initial_caller_message': initial_message
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
        
        # Generate response
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
            'conversation_history': updated_state.conversation_history[-4:]  # Last 4 exchanges
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"Client joined session {session_id}")

@socketio.on('leave_session')
def handle_leave_session(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        logger.info(f"Client left session {session_id}")

@socketio.on('call_taker_message')
def handle_call_taker_message(data):
    try:
        session_id = data.get('session_id')
        message = data.get('message', '')
        
        session = session_manager.get_session(session_id)
        if not session:
            emit('error', {'message': 'Session not found'})
            return

        def generate_response():
            try:
                caller_response, updated_state = generator.generate_response(
                    session.caller_state, message
                )
                
                session_manager.update_session(session_id, updated_state)
                
                logger.info(f"Generated response for {session_id}")
                
                socketio.emit('caller_response', {
                    'caller_response': caller_response,
                    'emotional_state': updated_state.emotional_state.value,
                    'intensity': updated_state.intensity,
                    'scenario_progress': updated_state.scenario_progress,
                    'key_details_revealed': updated_state.key_details_revealed
                }, room=session_id)
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                socketio.emit('error', {'message': 'Failed to generate response'}, room=session_id)

        # Start generation in a separate thread
        Thread(target=generate_response, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('error', {'message': 'Internal server error'})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': generator.model is not None,
        'active_sessions': len([s for s in sessions.values() if s.is_active])
    })

if __name__ == '__main__':
    logger.info("Starting 911 Call Simulation with Llama-3-70B")
    logger.info(f"Using local model at: {generator.model_path}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )
