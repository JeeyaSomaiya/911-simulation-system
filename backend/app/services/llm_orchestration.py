import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import redis
import queue
import threading

logger = logging.getLogger(__name__)

class EmotionalState:
    """Manages emotional state transitions"""
    
    STATES = ['CALM', 'WORRIED', 'PANICKED', 'HYSTERICAL', 'RELIEVED']
    
    def __init__(self):
        self.current_state = 'WORRIED'
        self.intensity = 5  # 1-10 scale
        self.state_history = []
        
    def update_state(self, call_taker_response: str, scenario_events: Dict, time_elapsed: int):
        """Update emotional state based on various factors"""
        # Simple rule-based state machine for demo
        # In production, this would be more sophisticated
        
        response_lower = call_taker_response.lower()
        
        # Positive responses reduce intensity
        if any(word in response_lower for word in ['help', 'okay', 'understand', 'calm']):
            self.intensity = max(1, self.intensity - 1)
        
        # Poor responses increase intensity  
        if any(word in response_lower for word in ['what', 'repeat', 'slow down']):
            self.intensity = min(10, self.intensity + 1)
        
        # Time factor - people generally get more anxious over time
        if time_elapsed > 300:  # 5 minutes
            self.intensity = min(10, self.intensity + 1)
        
        # Update state based on intensity
        if self.intensity <= 2:
            self.current_state = 'CALM'
        elif self.intensity <= 4:
            self.current_state = 'WORRIED' 
        elif self.intensity <= 7:
            self.current_state = 'PANICKED'
        else:
            self.current_state = 'HYSTERICAL'
        
        self.state_history.append({
            'state': self.current_state,
            'intensity': self.intensity,
            'timestamp': datetime.utcnow().isoformat()
        })

class LLMOrchestrationService:
    def __init__(self, model_path: str, use_gpu: bool = True):
        self.model_path = model_path
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        
        self.base_model = None
        self.tokenizer = None
        self.model = None
        
        self.active_sessions = {}
        self.redis_client = None
        
        # Scenario templates
        self.scenario_templates = {
            'house_fire': {
                'initial_state': 'PANICKED',
                'caller_profile': 'adult_female_30s',
                'background': 'House fire with family members potentially trapped',
                'key_information': {
                    'location': 'residential home',
                    'occupants': 'family of 4',
                    'immediate_danger': 'fire spreading',
                    'access_issues': 'front door blocked'
                }
            },
            'medical_emergency': {
                'initial_state': 'WORRIED',
                'caller_profile': 'adult_male_40s', 
                'background': 'Chest pain, possible heart attack',
                'key_information': {
                    'symptoms': 'chest pain, shortness of breath',
                    'medical_history': 'high blood pressure',
                    'current_status': 'conscious but in pain',
                    'medications': 'blood pressure medication'
                }
            },
            'robbery': {
                'initial_state': 'PANICKED',
                'caller_profile': 'adult_female_25s',
                'background': 'Armed robbery in progress at convenience store',
                'key_information': {
                    'location': 'convenience store',
                    'suspects': '2 males with handguns',
                    'victims': 'store clerk and 2 customers',
                    'current_status': 'suspects still on scene'
                }
            }
        }
        
    def initialize(self, redis_url: str):
        """Initialize the LLM service"""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(redis_url)
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                "meta-llama/Llama-2-7b-chat-hf",
                use_auth_token=True
            )
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load base model
            self.base_model = AutoModelForCausalLM.from_pretrained(
                "meta-llama/Llama-2-7b-chat-hf",
                torch_dtype=torch.float16 if self.use_gpu else torch.float32,
                device_map="auto" if self.use_gpu else None,
                use_auth_token=True
            )
            
            # Load fine-tuned model if available
            try:
                self.model = PeftModel.from_pretrained(
                    self.base_model,
                    self.model_path,
                    torch_dtype=torch.float16 if self.use_gpu else torch.float32
                )
                logger.info("Fine-tuned model loaded successfully")
            except:
                self.model = self.base_model
                logger.warning("Fine-tuned model not found, using base model")
            
            logger.info(f"LLM service initialized on device: {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    def start_session(self, session_id: str, scenario_type: str) -> Dict[str, Any]:
        """Start a new conversation session"""
        try:
            if scenario_type not in self.scenario_templates:
                raise ValueError(f"Unknown scenario type: {scenario_type}")
            
            scenario = self.scenario_templates[scenario_type]
            emotional_state = EmotionalState()
            emotional_state.current_state = scenario['initial_state']
            
            session_data = {
                'session_id': session_id,
                'scenario_type': scenario_type,
                'scenario': scenario,
                'emotional_state': emotional_state,
                'conversation_history': [],
                'context': scenario['key_information'].copy(),
                'start_time': datetime.utcnow(),
                'information_revealed': set(),
                'call_taker_performance': {
                    'questions_asked': 0,
                    'key_info_obtained': 0,
                    'rapport_building': 0
                }
            }
            
            self.active_sessions[session_id] = session_data
            
            # Store in Redis for persistence
            self.redis_client.setex(
                f"session:{session_id}",
                3600,  # 1 hour expiry
                json.dumps(session_data, default=str)
            )
            
            return {
                'session_id': session_id,
                'scenario_type': scenario_type,
                'initial_state': emotional_state.current_state,
                'caller_profile': scenario['caller_profile']
            }
            
        except Exception as e:
            logger.error(f"Error starting session {session_id}: {e}")
            raise
    
    def generate_response(self, session_id: str, call_taker_input: str, 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate caller response based on call taker input"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            scenario = session['scenario']
            emotional_state = session['emotional_state']
            
            # Update emotional state
            time_elapsed = (datetime.utcnow() - session['start_time']).total_seconds()
            emotional_state.update_state(call_taker_input, {}, time_elapsed)
            
            # Build conversation context
            conversation_context = self._build_conversation_context(session, call_taker_input)
            
            # Generate response using the model
            response_text = self._generate_text(conversation_context, emotional_state)
            
            # Update conversation history
            session['conversation_history'].append({
                'role': 'dispatcher',
                'content': call_taker_input,
                'timestamp': datetime.utcnow()
            })
            
            session['conversation_history'].append({
                'role': 'caller',
                'content': response_text,
                'emotional_state': emotional_state.current_state,
                'intensity': emotional_state.intensity,
                'timestamp': datetime.utcnow()
            })
            
            # Update Redis
            self.redis_client.setex(
                f"session:{session_id}",
                3600,
                json.dumps(session, default=str)
            )
            
            return {
                'session_id': session_id,
                'response': response_text,
                'emotional_state': emotional_state.current_state,
                'intensity': emotional_state.intensity,
                'scenario_compliance': self._check_scenario_compliance(session, response_text),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response for session {session_id}: {e}")
            return {
                'session_id': session_id,
                'response': "I'm sorry, can you repeat that?",
                'emotional_state': 'WORRIED',
                'intensity': 5,
                'error': str(e)
            }
    
    def _build_conversation_context(self, session: Dict, current_input: str) -> str:
        """Build conversation context for the model"""
        scenario = session['scenario']
        emotional_state = session['emotional_state']
        
        # System prompt with scenario and emotional context
        system_prompt = f"""You are simulating a 911 emergency caller in a {session['scenario_type']} scenario.

Scenario: {scenario['background']}
Caller Profile: {scenario['caller_profile']}
Current Emotional State: {emotional_state.current_state} (intensity: {emotional_state.intensity}/10)

Key Information to Reveal:
{json.dumps(scenario['key_information'], indent=2)}

Guidelines:
- Stay in character as the caller
- Respond naturally based on your emotional state
- Gradually reveal information when asked appropriate questions
- Don't volunteer all information at once
- React realistically to dispatcher questions and instructions
- Maintain emotional consistency

Recent conversation:"""

        # Add recent conversation history
        for turn in session['conversation_history'][-6:]:  # Last 3 exchanges
            role = "Dispatcher" if turn['role'] == 'dispatcher' else "Caller"
            system_prompt += f"\n{role}: {turn['content']}"
        
        system_prompt += f"\nDispatcher: {current_input}\nCaller:"
        
        return system_prompt
    
    def _generate_text(self, context: str, emotional_state: EmotionalState) -> str:
        """Generate text using the language model"""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                context,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            if self.use_gpu:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.7 + (emotional_state.intensity * 0.05),  # More random when emotional
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()
            
            # Post-process response based on emotional state
            response = self._post_process_response(response, emotional_state)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return "I... I'm sorry, can you help me?"
    
    def _post_process_response(self, response: str, emotional_state: EmotionalState) -> str:
        """Post-process response based on emotional state"""
        # Add emotional markers based on state
        if emotional_state.current_state == 'PANICKED':
            if not any(marker in response.lower() for marker in ['!', 'please', 'help']):
                response = response.rstrip('.') + "!"
        
        elif emotional_state.current_state == 'HYSTERICAL':
            response = response.upper() if emotional_state.intensity > 8 else response
            if not response.endswith(('!', '?')):
                response += "!!"
        
        elif emotional_state.current_state == 'CALM':
            # Remove excessive punctuation for calm responses
            response = response.replace('!!', '.').replace('!', '.')
        
        return response
    
    def _check_scenario_compliance(self, session: Dict, response: str) -> float:
        """Check if response complies with scenario requirements"""
        # Simple compliance check - in production this would be more sophisticated
        scenario_keywords = []
        for value in session['scenario']['key_information'].values():
            if isinstance(value, str):
                scenario_keywords.extend(value.lower().split())
        
        response_words = response.lower().split()
        compliance_score = len(set(scenario_keywords) & set(response_words)) / len(scenario_keywords)
        
        return min(compliance_score * 2, 1.0)  # Scale to 0-1
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Calculate final metrics
            end_time = datetime.utcnow()
            duration = (end_time - session['start_time']).total_seconds()
            
            final_metrics = {
                'session_id': session_id,
                'duration': duration,
                'total_exchanges': len(session['conversation_history']) // 2,
                'emotional_progression': session['emotional_state'].state_history,
                'final_emotional_state': session['emotional_state'].current_state,
                'scenario_type': session['scenario_type']
            }
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Remove from Redis
            self.redis_client.delete(f"session:{session_id}")
            
            return final_metrics
        
        return {'error': 'Session not found'}

# Global service instance
llm_service = LLMOrchestrationService("", True)
