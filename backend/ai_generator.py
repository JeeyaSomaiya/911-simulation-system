import logging
import torch
import re
import random
import spacy
from datetime import datetime
from typing import Tuple, List, Dict
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
        self.nlp = self._load_spacy_model()
        self.lock = Lock()
        self.load_model()
        logger.info("Hugging Face Llama-3.1-8B Caller Generator initialized")
    
    def _load_spacy_model(self):
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully")
            return nlp
        except OSError:
            try:
                logger.warning("spaCy model 'en_core_web_sm' not found. Trying to download...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model 'en_core_web_sm' downloaded and loaded successfully")
                return nlp
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}. Using fallback text processing.")
                return None
    
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
                    max_new_tokens=100,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                    repetition_penalty=1.2,
                )
                
                response = outputs[0]['generated_text'][len(messages):].strip()
            
            response = self._clean_response(response, call_taker_message, caller_state.emotional_state, caller_state)
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
        
        for exchange in caller_state.conversation_history:
            if exchange['role'] == 'call_taker':
                messages.append({"role": "user", "content": exchange['content']})
            elif exchange['role'] == 'caller':
                messages.append({"role": "assistant", "content": exchange['content']})
        
        emotional_context = self._get_emotional_context(caller_state.emotional_state)
        
        current_question_instruction = f"""
IMPORTANT: The 911 operator just asked: "{call_taker_message}"
{emotional_context}
Answer this question clearly and concisely based on what you can see.
Focus on providing a complete, coherent response that directly addresses the question.
"""
        
        messages.append({"role": "user", "content": current_question_instruction})
        
        formatted_messages = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return formatted_messages
    
    def _get_emotional_context(self, emotional_state: EmotionalState) -> str:
        emotional_contexts = {
            EmotionalState.CALM: "You're relatively calm but concerned. Speak clearly and coherently.",
            EmotionalState.WORRIED: "You're worried but trying to stay focused. Your voice might show some tension but you're still coherent.",
            EmotionalState.PANICKED: "You're panicked but still able to communicate clearly. Speak with urgency but maintain complete sentences.",
            EmotionalState.HYSTERICAL: "You're extremely upset but still trying to communicate effectively. Your speech might be rushed but should still be understandable.",
            EmotionalState.RELIEVED: "You're starting to calm down as help arrives. Speak clearly and provide complete information."
        }
        return emotional_contexts.get(emotional_state, "You're concerned but trying to communicate clearly.")
    
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
        
        scenario_details = self._get_scenario_specific_prompt(context)
        
        return f"""You are {context['caller_name']} calling 911. You witnessed: {context['situation']}

Location: {context['location']}
Your phone: {context['phone']}
Current emotional state: {caller_state.emotional_state.value}
{role_clarification}

SCENARIO-SPECIFIC DETAILS:
{scenario_details}

CRITICAL RESPONSE GUIDELINES:
1. Speak in COMPLETE, COHERENT sentences - no trailing off or fragmented thoughts
2. Use natural but clear language - avoid excessive exclamation marks or emotional outbursts
3. Answer questions directly and completely
4. If you don't know something, say "I'm not sure" or "I can't really tell from here"
5. Keep responses focused and to the point - 1-2 clear sentences
6. NEVER describe your physical state or emotions directly
7. Show appropriate concern through your word choice, not through excessive punctuation
8. Use normal conversational patterns: "looks like", "seems like", "I think"
9. Stay in character as {context['caller_name']} - a concerned but coherent witness

IMPORTANT: MAINTAIN CLEAR COMMUNICATION
- Always speak in complete sentences
- Avoid trailing off mid-thought (...)
- Use exclamation marks sparingly and appropriately
- Don't repeat yourself unnecessarily
- Provide information in a logical, organized way

CRITICAL: DO NOT VOLUNTEER DETAILS UNLESS ASKED!
- For the first response, ONLY state the emergency and basic location
- Wait for the operator to ask questions before providing details
- Only answer the specific question asked

NATURAL SPEECH EXAMPLES:
- "There's been a car accident at Deerfoot and Cranston!"
- "I just saw a white SUV roll over into the ditch."
- "I'm not sure if anyone's hurt yet."
- "It looks like there might be black ice on the road."

SPECIAL: If asked "911, what is your emergency?" respond ONLY with: {initial_question_response}"""

    def _get_scenario_specific_prompt(self, context: dict) -> str:
        scenario_type = context.get('scenario_type', '')
        scenario_type_lower = scenario_type.lower()
        
        if 'accident' in scenario_type_lower or 'crash' in scenario_type_lower or 'collision' in scenario_type_lower:
            return """ACCIDENT-SPECIFIC DETAILS:
- Note vehicle types, colors, what happened
- Observe injuries, trapped people, hazards
- Notice fluid leaks, airbags, damage
- Count people involved, their conditions
- Identify immediate dangers
- Note vehicle positions and damage
- Observe road conditions"""
        
        elif 'fire' in scenario_type_lower:
            return """FIRE-SPECIFIC DETAILS:
- Note size, location, spread of fire
- Observe smoke color and direction
- Identify potential victims or trapped people
- Notice hazards
- Check for evacuation status
- Note building type"""
        
        elif 'medical' in scenario_type_lower or 'injury' in scenario_type_lower:
            return """MEDICAL-SPECIFIC DETAILS:
- Note if people are awake or unconscious
- Observe breathing problems
- Identify visible injuries, bleeding
- Note approximate age and condition
- Check for medical alerts
- Observe responsiveness"""
        
        elif 'crime' in scenario_type_lower or 'robbery' in scenario_type_lower or 'assault' in scenario_type_lower:
            return """CRIME-SPECIFIC DETAILS:
- Note suspect descriptions: height, build, clothing
- Observe weapons, direction they went, vehicles
- Identify victims and their conditions
- Notice time it happened
- Note any distinctive features
- Observe where they went"""
        
        return "Describe what you're seeing clearly and concisely."

    def _get_initial_question_response(self, context: dict, caller_state: CallerState) -> str:
        scenario_type = context.get('scenario_type', '')
        
        if 'accident' in scenario_type.lower():
            natural_responses = [
                "There's been a car accident at {location}!",
                "Car crash at {location}!",
                "There's a wreck at {location}!",
                "Accident at {location}!",
                "Car accident at {location}!"
            ]
            response = random.choice(natural_responses)
            return response.format(location=context['location'])
        
        elif 'fire' in scenario_type.lower():
            natural_responses = [
                "There's a fire at {location}!",
                "Building on fire at {location}!",
                "Fire emergency at {location}!",
                "Fire at {location}!",
                "Structure fire at {location}!"
            ]
            response = random.choice(natural_responses)
            return response.format(location=context['location'])
        
        elif 'medical' in scenario_type.lower():
            natural_responses = [
                "Medical emergency at {location}!",
                "Someone needs help at {location}!",
                "Medical situation at {location}!",
                "Health emergency at {location}!",
                "Injury at {location}!"
            ]
            response = random.choice(natural_responses)
            return response.format(location=context['location'])
        
        return context.get('initial_response', "Emergency at {location}!").format(location=context['location'])

    def _clean_response(self, response: str, question: str = "", emotional_state: EmotionalState = None, caller_state: CallerState = None) -> str:
        artifacts = ["<|eot_id|>", "<|end_of_text|>", "<|start_header_id|>", "<|end_header_id|>", "*", "**", "`", "\"\"\""]
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        prefixes = ["assistant", "911 caller:", "Response:", "Caller:", "A:", "User:", "AI:", "The caller says:", "I would say:"]
        for prefix in prefixes:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        response = response.replace("assistant", "").strip()
        
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]
        
        response = re.sub(r'^"+|"+$', '', response)
        
        response = self._fix_punctuation_and_trailing_off(response)
        
        if len(response.split()) < 3 or not response.strip():
            response = "I can see what's happening from here."
        
        response = re.sub(r'\(.*?\)', '', response)
        response = re.sub(r'\[.*?\]', '', response)
        
        response = self._remove_emotional_indicators(response)
        
        response = self._naturalize_language(response, emotional_state)
        
        if caller_state and len(caller_state.conversation_history) == 0:
            response = self._limit_first_response(response, question)
        
        if question and not self._validate_response_addresses_question(question, response):
            response = self._generate_direct_response(question, response, emotional_state)
        
        return response.strip()
    
    def _fix_punctuation_and_trailing_off(self, response: str) -> str:
        response = re.sub(r'\.\.\.+', '.', response)
        response = re.sub(r'\.\s*\.', '.', response)
        response = re.sub(r'\.\s+$', '.', response)
        
        response = re.sub(r'!+', '!', response)
        response = re.sub(r'!\s*!', '!', response)
        
        response = re.sub(r'[!?]\.', '!', response)
        response = re.sub(r'\.!', '!', response)
        
        if not response.endswith(('.', '!', '?')):
            sentences = re.split(r'[.!?]', response)
            if sentences and sentences[-1].strip():
                response = response + '.'
            else:
                response = response.rstrip() + '.'
        
        response = re.sub(r',\s*\.\.\.', ',', response)
        response = re.sub(r'\s+\.\.\.', '.', response)
        
        response = re.sub(r'([.!?])\1+', r'\1', response)
        
        return response
    
    def _limit_first_response(self, response: str, question: str) -> str:
        if "911, what is your emergency" in question.lower() or "what is your emergency" in question.lower():
            response_words = response.split()
            if len(response_words) > 12:
                for i in range(min(10, len(response_words)), len(response_words)):
                    if response_words[i].endswith(('.', '!', '?')):
                        response = ' '.join(response_words[:i+1])
                        break
                else:
                    response = ' '.join(response_words[:12]) + '...'
            
            detailed_phrases = [
                'looks like', 'seems like', 'appears to be', 'i think', 'i believe',
                'one car', 'another car', 'both cars', 'vehicles', 'accident type',
                'injured', 'hurt', 'damage', 'wrecked', 'rolled over', 'flipped',
                'black ice', 'cause', 'reason', 'because'
            ]
            
            for phrase in detailed_phrases:
                if phrase in response.lower():
                    first_sentence = response.split('.')[0] + '.'
                    if len(first_sentence.split()) >= 4:
                        response = first_sentence
                    break
        
        return response
    
    def _remove_emotional_indicators(self, response: str) -> str:
        words = response.split()
        filtered_words = []
        
        emotional_descriptors = [
            "nervous", "scared", "terrified", "panicked", "hysterical",
            "frightened", "anxious", "worried", "stressed", "upset",
            "distraught", "agitated", "frantic", "desperate", "shaken",
            "traumatized", "shocked", "alarmed", "apprehensive"
        ]
        
        for word in words:
            if word.endswith('ly') and len(word) > 4 and word not in ['only', 'really', 'actually']:
                continue
            if word.lower() in emotional_descriptors:
                continue
            filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _naturalize_language(self, response: str, emotional_state: EmotionalState = None) -> str:
        natural_replacements = {
            r'\bvehicle\b': 'car',
            r'\bvehicles\b': 'cars',
            r'\bautomobile\b': 'car',
            r'\bnon-injury accident\b': 'accident',
            r'\bnon-injury collision\b': 'crash',
            r'\bmotor vehicle collision\b': 'car accident',
            r'\bappear to be\b': 'seem to be',
            r'\bappears to be\b': 'seems to be',
            r'\bindividuals\b': 'people',
            r'\bpersons\b': 'people',
            r'\bpedestrians\b': 'people walking',
            r'\boccupants\b': 'people in the car',
            r'\bdriveable\b': 'able to drive',
            r'\boperable\b': 'working',
            r'\bfunctional\b': 'working',
            r'\bconscious\b': 'awake',
            r'\bunconscious\b': 'passed out',
            r'\bhemorrhaging\b': 'bleeding badly',
            r'\bfractured\b': 'broken',
            r'\blaceration\b': 'cut',
            r'\bcontusion\b': 'bruise',
            r'\bambulate\b': 'walk',
            r'\btransport\b': 'take',
            r'\brequesting\b': 'needing',
            r'\brequire\b': 'need',
            r'\butilize\b': 'use',
            r'\bapproximately\b': 'about',
            r'\bassistance\b': 'help',
            r'\brespond\b': 'come',
            r'\bunit\b': 'car',
            r'\boffice\b': 'police officer',
            r'\bemergency medical services\b': 'ambulance',
            r'\bparamedics\b': 'ambulance crew',
        }
        
        for formal, natural in natural_replacements.items():
            response = re.sub(formal, natural, response, flags=re.IGNORECASE)
        
        conversational_patterns = [
            (r'\bI (saw|observed|witnessed)\b', 'I just saw'),
            (r'\bthere is\b', "there's"),
            (r'\bthere are\b', "there're"),
            (r'\bI am\b', "I'm"),
            (r'\bdo not\b', "don't"),
            (r'\bdoes not\b', "doesn't"),
            (r'\bcan not\b', "can't"),
            (r'\bcould not\b', "couldn't"),
            (r'\bwill not\b', "won't"),
            (r'\bwould not\b', "wouldn't"),
            (r'\bhave not\b', "haven't"),
            (r'\bhas not\b', "hasn't"),
        ]
        
        for pattern, replacement in conversational_patterns:
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        response = re.sub(r'One (.*?) has been', r'A \1 got', response)
        response = re.sub(r'Both (.*?) seem', r'Both \1 look like they\'re', response)
        response = re.sub(r'All parties', r'Everyone', response)
        response = re.sub(r'The driver of the', r'The person driving the', response)
        
        response = re.sub(r'appear to be okay', r'seem okay', response)
        response = re.sub(r'appears to be conscious', r'seems awake', response)
        response = re.sub(r'bleeding profusely', r'bleeding a lot', response)
        
        if emotional_state in [EmotionalState.PANICKED, EmotionalState.HYSTERICAL]:
            response = self._add_emotional_urgency(response)
        
        return response
    
    def _add_emotional_urgency(self, response: str) -> str:
        urgent_patterns = [
            (r'\.(?!\w)', '!'),
            (r'There\'s', "There's just"),
            (r'It looks', "It really looks")
        ]
        
        for pattern, replacement in urgent_patterns:
            response = re.sub(pattern, replacement, response)
        
        urgent_prefixes = [
            "Oh my god, ",
            "Seriously, ",
            "I can't believe it, "
        ]
        
        if random.random() < 0.2:
            response = random.choice(urgent_prefixes) + response.lower()
        
        return response

    def _validate_response_addresses_question(self, question: str, response: str) -> bool:
        question_lower = question.lower()
        response_lower = response.lower()
        
        question_types = {
            'safe': ['safe', 'okay', 'alright', 'unhurt', 'injured', 'hurt'],
            'location': ['where', 'location', 'address', 'area', 'place'],
            'people': ['people', 'person', 'victim', 'individual', 'man', 'woman', 'child', 'driver', 'passenger'],
            'vehicle': ['vehicle', 'car', 'truck', 'suv', 'van', 'motorcycle', 'bicycle'],
            'hazard': ['hazard', 'danger', 'leak', 'fire', 'smoke', 'wire', 'fluid', 'spill', 'chemical'],
            'medical': ['medical', 'ambulance', 'hurt', 'injured', 'wounded', 'bleeding', 'conscious', 'breathing'],
            'count': ['many', 'much', 'number', 'count', 'how many', 'how much', 'total'],
            'description': ['describe', 'look like', 'color', 'model', 'type', 'kind', 'make', 'appearance']
        }
        
        for q_type, keywords in question_types.items():
            if any(kw in question_lower for kw in keywords):
                if not any(kw in response_lower for kw in keywords):
                    return False
        
        if question_lower.startswith(('is ', 'are ', 'do ', 'does ', 'did ', 'was ', 'were ', 'has ', 'have ', 'can ', 'could ')):
            if not any(word in response_lower for word in ['yes', 'no', 'not sure', 'i think', 'probably', 'maybe', 'i believe', 'it seems']):
                return False
        
        if 'how many' in question_lower and not any(word.isdigit() for word in response_lower.split()):
            return False
            
        if 'what color' in question_lower and not any(color_word in response_lower for color_word in ['white', 'black', 'red', 'blue', 'green', 'yellow', 'silver', 'gray', 'brown']):
            return False
        
        return True

    def _generate_direct_response(self, question: str, original_response: str, emotional_state: EmotionalState = None) -> str:
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['is ', 'are ', 'do ', 'does ', 'did ', 'was ', 'were ', 'has ', 'have ']):
            if 'not' in original_response.lower() or 'no ' in original_response.lower() or "don't" in original_response.lower():
                return "No, " + original_response
            else:
                return "Yes, " + original_response
        
        elif 'how many' in question_lower:
            if any(word.isdigit() for word in original_response.split()):
                return original_response
            return "I'd say " + original_response
        
        elif 'where' in question_lower:
            if any(loc_word in original_response.lower() for loc_word in ['here', 'there', 'street', 'road', 'avenue', 'highway']):
                return original_response
            return "It's " + original_response
        
        elif 'what color' in question_lower:
            if any(color_word in original_response.lower() for color_word in ['white', 'black', 'red', 'blue', 'green', 'yellow']):
                return original_response
            return "Looks like " + original_response
        
        return original_response
    
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
            'location': ['where', 'location', 'address', 'street', 'avenue', 'road', 'highway', 'intersection'],
            'situation': ['happened', 'wrong', 'emergency', 'problem', 'issue', 'occurred'],
            'people': ['anyone', 'people', 'others', 'children', 'person', 'victim', 'individual', 'driver', 'passenger'],
            'medical': ['hurt', 'injured', 'medical', 'conscious', 'bleeding', 'breathing', 'wounded', 'ambulance'],
            'contact': ['phone', 'number', 'contact', 'callback', 'call you back', 'reach you'],
            'details': ['describe', 'look like', 'color', 'model', 'type', 'kind', 'make', 'appearance'],
            'vehicle': ['vehicle', 'car', 'truck', 'suv', 'van', 'motorcycle', 'license', 'plate'],
            'hazards': ['hazard', 'danger', 'leak', 'fire', 'smoke', 'wire', 'fluid', 'chemical', 'spill']
        }
        
        for detail, keywords in question_types.items():
            if any(kw in call_taker_message.lower() for kw in keywords):
                if detail not in new_state.key_details_revealed:
                    new_state.key_details_revealed.append(detail)
                    new_state.scenario_progress = min(1.0, new_state.scenario_progress + 0.15)
        
        question_quality = self._assess_response_quality(call_taker_message, response)
        
        if "calm down" in call_taker_message.lower() or "stay calm" in call_taker_message.lower():
            new_state.intensity = max(1, new_state.intensity - 1)
        elif "help is coming" in call_taker_message.lower() or "on the way" in call_taker_message.lower():
            new_state.intensity = max(3, new_state.intensity - 2)
        elif "urgent" in response.lower() or "quickly" in response.lower() or "hurry" in response.lower():
            new_state.intensity = min(10, new_state.intensity + 1)
        
        if question_quality < 0.5:
            new_state.intensity = min(10, new_state.intensity + 0.5)
        elif question_quality > 0.8:
            new_state.intensity = max(1, new_state.intensity - 0.3)
        
        if new_state.intensity <= 3:
            new_state.emotional_state = EmotionalState.RELIEVED
        elif new_state.intensity <= 5:
            new_state.emotional_state = EmotionalState.WORRIED
        elif new_state.intensity <= 8:
            new_state.emotional_state = EmotionalState.PANICKED
        else:
            new_state.emotional_state = EmotionalState.HYSTERICAL
        
        return new_state

    def _assess_response_quality(self, question: str, response: str) -> float:
        if not question.strip():
            return 0.8
        
        if self.nlp is None:
            return self._fallback_assess_response_quality(question, response)
        
        try:
            doc_question = self.nlp(question.lower())
            doc_response = self.nlp(response.lower())
            
            question_nouns = {token.lemma_ for token in doc_question if token.pos_ in ['NOUN', 'PROPN']}
            response_nouns = {token.lemma_ for token in doc_response if token.pos_ in ['NOUN', 'PROPN']}
            
            question_verbs = {token.lemma_ for token in doc_question if token.pos_ == 'VERB'}
            response_verbs = {token.lemma_ for token in doc_response if token.pos_ == 'VERB'}
            
            noun_overlap = len(question_nouns.intersection(response_nouns)) / len(question_nouns) if question_nouns else 0
            verb_overlap = len(question_verbs.intersection(response_verbs)) / len(question_verbs) if question_verbs else 0
            
            overlap = (noun_overlap + verb_overlap) / 2
            
            if any(word in question.lower() for word in ['how many', 'number', 'count']):
                has_number = any(token.like_num for token in doc_response)
                return 0.8 if has_number else 0.3
            
            elif any(word in question.lower() for word in ['where', 'location', 'address']):
                location_ents = any(ent.label_ in ['GPE', 'LOC', 'FAC'] for ent in doc_response.ents)
                location_words = any(word in response.lower() for word in ['here', 'there', 'street', 'avenue', 'road', 'highway', 'deerfoot', 'intersection'])
                return 0.9 if (location_ents or location_words) else 0.4
            
            elif any(word in question.lower() for word in ['what color', 'color']):
                color_words = ['white', 'black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'brown', 'gray', 'silver']
                has_color = any(word in response.lower() for word in color_words)
                return 0.9 if has_color else 0.3
            
            elif question.lower().startswith(('is ', 'are ', 'do ', 'does ', 'did ', 'was ', 'were ', 'has ', 'have ')):
                has_yes_no = any(word in response.lower() for word in ['yes', 'no', 'not sure', 'i think', 'probably', 'maybe'])
                return 0.8 if has_yes_no else 0.4
            
            return min(1.0, overlap * 1.5)
        except Exception as e:
            logger.warning(f"spaCy processing failed: {e}. Using fallback assessment.")
            return self._fallback_assess_response_quality(question, response)
    
    def _fallback_assess_response_quality(self, question: str, response: str) -> float:
        question_lower = question.lower()
        response_lower = response.lower()
        
        question_words = set(question_lower.split())
        response_words = set(response_lower.split())
        
        overlap = len(question_words.intersection(response_words)) / len(question_words) if question_words else 0
        
        if any(word in question_lower for word in ['how many', 'number', 'count']):
            has_number = any(word.isdigit() for word in response_lower.split())
            return 0.8 if has_number else 0.3
        
        elif any(word in question_lower for word in ['where', 'location', 'address']):
            location_words = ['here', 'there', 'street', 'avenue', 'road', 'highway', 'deerfoot', 'intersection']
            has_location = any(word in response_lower for word in location_words)
            return 0.9 if has_location else 0.4
        
        elif any(word in question_lower for word in ['what color', 'color']):
            color_words = ['white', 'black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'brown', 'gray', 'silver']
            has_color = any(word in response_lower for word in color_words)
            return 0.9 if has_color else 0.3
        
        elif question_lower.startswith(('is ', 'are ', 'do ', 'does ', 'did ', 'was ', 'were ', 'has ', 'have ')):
            has_yes_no = any(word in response_lower for word in ['yes', 'no', 'not sure', 'i think', 'probably', 'maybe'])
            return 0.8 if has_yes_no else 0.4
        
        return min(1.0, overlap * 1.5)

    def generate_initial_response(self, scenario_type: ScenarioType) -> str:
        context = self.scenario_contexts.get(scenario_type)
        if not context:
            return "Help! There's an emergency!"
        
        return context.get('initial_response', "Help! There's an emergency!")
        