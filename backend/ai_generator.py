import logging
import torch
from datetime import datetime
from typing import Tuple
from threading import Lock
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from models import CallerState, ScenarioType, EmotionalState
from scenario_contexts import load_scenario_contexts

logger = logging.getLogger(__name__)

class HuggingFaceCallerGenerator:
    def __init__(self):
        self.model_path = "/home/ubuntu/.llama/checkpoints/Llama3.1-8B-Instruct-hf"
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.scenario_contexts = load_scenario_contexts()
        self.lock = Lock()
        self.load_model()
        logger.info("Hugging Face Llama-3.1-8B Caller Generator initialized")
    
    def load_model(self):
        try:
            logger.info(f"Loading Llama-3.1-8B model from: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            if self.tokenizer.chat_template is None:
                self.tokenizer.chat_template = "{% set loop_messages = messages %}{% for message in loop_messages %}{% set content = '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' %}{% if loop.index0 == 0 %}{% set content = '<|begin_of_text|>' + content %}{% endif %}{{ content }}{% endfor %}{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map="auto",
                torch_dtype=torch.bfloat16
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto"
            )
            
            logger.info("Llama-3.1-8B model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error("Please verify model path and available resources")
            raise RuntimeError("Model loading failed")

    def generate_response(self, caller_state: CallerState, call_taker_message: str) -> Tuple[str, CallerState]:
        context = self.scenario_contexts.get(caller_state.scenario_type)
        if not context:
            logger.error(f"No context for scenario: {caller_state.scenario_type}")
            return "I need help!", caller_state
        
        try:
            messages = self._build_messages(caller_state, call_taker_message, context)
            
            with self.lock:
                outputs = self.pipeline(
                    messages,
                    max_new_tokens=75,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                    repetition_penalty=1.2,
                )
                
                response = outputs[0]['generated_text'][len(messages):].strip()
            
            response = self._clean_response(response)
            new_state = self._update_state(caller_state, call_taker_message, response)
            
            return response, new_state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I need help!", caller_state
    
    def _build_messages(self, caller_state: CallerState, call_taker_message: str, context: dict) -> str:
        system_prompt = self._create_system_prompt(caller_state, context)
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for exchange in caller_state.conversation_history[-6:]:
            role = "user" if exchange['role'] == 'call_taker' else "assistant"
            messages.append({"role": role, "content": exchange['content']})
        
        messages.append({"role": "user", "content": call_taker_message})
        
        formatted_messages = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return formatted_messages
    
    def _create_system_prompt(self, caller_state: CallerState, context: dict) -> str:
        initial_question_response = self._get_initial_question_response(context, caller_state)
        
        role_clarification = ""
        if "witness" in context['caller_background'].lower() or "bystander" in context['caller_background'].lower():
            role_clarification = (
                "CRITICAL: YOU ARE A WITNESS ONLY, NOT INVOLVED IN THE INCIDENT. "
                "DO NOT CLAIM PERSONAL INVOLVEMENT OR INJURY. "
                "YOU ONLY SAW WHAT HAPPENED BUT WERE NOT A PARTICIPANT. "
                "RESPOND AS AN OBSERVER, NOT AS A VICTIM OR PARTICIPANT."
            )
        
        return f"""You are {context['caller_name']} calling 911. You witnessed: {context['situation']}

Location: {context['location']}
Your phone: {context['phone']}
Emotional state: {caller_state.emotional_state.value}
{role_clarification}

You are a real person reporting an emergency. Respond ONLY with what you would actually say to a 911 operator:
- Keep responses to 1-2 natural sentences
- NEVER describe your physical actions or state (e.g., no "breathing quickly", "crying", etc.)
- Express emotion through speech patterns, not descriptions
- DO NOT volunteer detailed information upfront
- Only provide specific details when asked
- Stay in character as {context['caller_name']}

SPECIAL: If asked "911, what is your emergency?" respond ONLY with: {initial_question_response}"""

    def _get_initial_question_response(self, context: dict, caller_state: CallerState) -> str:
        return context.get('initial_response', "I need help!")

    def _clean_response(self, response: str) -> str:
        artifacts = ["<|eot_id|>", "<|end_of_text|>", "<|start_header_id|>", "<|end_header_id|>", "*"]
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        prefixes = ["assistant", "911 caller:", "Response:", "Caller:", "A:", "User:"]
        for prefix in prefixes:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        response = response.replace("assistant", "").strip()
        
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]
        
        if response.endswith('. .') or response.endswith('..'):
            response = response.rstrip('. ')
        
        if len(response.split()) < 3 or not response.strip():
            return "It's on Deerfoot Trail."
        
        response = response.replace('. .', '.').replace('..', '.')
        
        if '(' in response and ')' in response:
            start = response.find('(')
            end = response.find(')', start)
            if end != -1:
                response = response[:start] + response[end+1:]
                
        forbidden_phrases = [
            "breathing quickly", "taking deep breaths", "shaking", 
            "crying", "sobbing", "hyperventilating", "pacing", 
            "holding my chest", "clutching my heart"
        ]
        for phrase in forbidden_phrases:
            response = response.replace(phrase, "")
        
        return response.strip()
    
    def _update_state(self, caller_state: CallerState, call_taker_message: str, response: str) -> CallerState:
        new_state = CallerState(
            emotional_state=caller_state.emotional_state,
            intensity=caller_state.intensity,
            scenario_type=caller_state.scenario_type,
            key_details_revealed=caller_state.key_details_revealed.copy(),
            conversation_history=caller_state.conversation_history.copy(),
            caller_profile=caller_state.caller_profile.copy(),
            scenario_progress=caller_state.scenario_progress
        )
        
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
        
        question_types = {
            'location': ['where', 'location', 'address'],
            'situation': ['happened', 'wrong', 'emergency'],
            'people': ['anyone', 'people', 'others', 'children'],
            'medical': ['hurt', 'injured', 'medical', 'conscious'],
            'contact': ['phone', 'number', 'contact', 'callback'],
            'details': ['describe', 'look like', 'color', 'model']
        }
        
        for detail, keywords in question_types.items():
            if any(kw in call_taker_message.lower() for kw in keywords):
                if detail not in new_state.key_details_revealed:
                    new_state.key_details_revealed.append(detail)
                    new_state.scenario_progress = min(1.0, new_state.scenario_progress + 0.15)
        
        if "calm down" in call_taker_message.lower():
            new_state.intensity = max(1, new_state.intensity - 1)
        elif "help is coming" in call_taker_message.lower() or "on the way" in call_taker_message.lower():
            new_state.intensity = max(3, new_state.intensity - 2)
        elif "urgent" in response.lower() or "quickly" in response.lower():
            new_state.intensity = min(10, new_state.intensity + 1)
        
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
        context = self.scenario_contexts.get(scenario_type)
        if not context:
            return "Help! There's an emergency!"
        
        return context.get('initial_response', "Help! There's an emergency!")
        