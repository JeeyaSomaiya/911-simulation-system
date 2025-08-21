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
from scenario_contexts import load_scenario_contexts, get_random_scenario_context

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
        context = caller_state.caller_profile.get('selected_context')
        if not context:
            logger.error(f"No stored context for session.")
        
        try:
            messages = self._build_messages(caller_state, call_taker_message, context)
            
            with self.lock:
                outputs = self.pipeline(
                    messages,
                    max_new_tokens=256,  # Shorter responses
                    do_sample=True,
                    temperature=0.4,     # Balanced - not too creative, not too robotic
                    top_p=0.85,         
                    eos_token_id=self.tokenizer.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id,
                    repetition_penalty=1.1,
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
        
        current_question_instruction = f"""The 911 operator asked: "{call_taker_message}"

Answer based only on the scenario information above."""
        
        messages.append({"role": "user", "content": current_question_instruction})
        
        formatted_messages = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return formatted_messages
    
    def _get_emotional_context(self, emotional_state: EmotionalState) -> str:
        emotional_contexts = {
            EmotionalState.CALM: "You're relatively calm but concerned. Speak naturally and coherently.",
            EmotionalState.WORRIED: "You're worried but trying to stay focused. Your voice might show some tension but you're still coherent.",
            EmotionalState.PANICKED: "You're panicked but still able to communicate. Speak with urgency but maintain complete sentences.",
            EmotionalState.HYSTERICAL: "You're extremely upset but still trying to communicate. Your speech might be rushed but should still be understandable.",
            EmotionalState.RELIEVED: "You're starting to calm down as help arrives. Speak clearly and provide complete information."
        }
        return emotional_contexts.get(emotional_state, "You're concerned but trying to communicate clearly.")
    
    def _create_system_prompt(self, caller_state: CallerState, context: dict) -> str:
        is_first_response = len(caller_state.conversation_history) == 0
        
        if is_first_response:
            return f"""You are {context.get('caller_name', '')} calling 911. You've been in an accident.

For your first response, just say something brief like "I've been in an accident" or "I need help, there's been a car accident." Don't give details yet."""
        
        return f"""You are {context.get('caller_name', '')} calling 911 about an accident.

Scenario details: {context.get('situation', '')}
Location: {context.get('location', '')}
Your role: {context.get('caller_background', '')}
Current status: {context.get('current_status', '')}
Your phone: {context.get('phone', '')}

Key principles:
- When asked "what happened", give a short 2-sentence summary only and do NOT give any specific details from the scenario, only a generalized overview of the situation 
- Wait for the operator to ask specific questions before giving details
- Real people don't recite every fact at once
- Answer only what was specifically asked
- Keep each response to one main point

Examples:
- "What happened?" → "I crashed my car" (not a full story)
- "Where are you?" → Give the location
- "Are you hurt?" → Answer about injuries
- "What's your phone number?" → Give the number"""

    def _get_scenario_specific_prompt(self, context: dict) -> str:
        return """You can only describe what is explicitly stated in your scenario facts above. Do not add details."""
    
    def _clean_response(self, response: str, question: str = "", emotional_state: EmotionalState = None, caller_state: CallerState = None) -> str:
        # Remove AI artifacts and prefixes
        artifacts = ["<|eot_id|>", "<|end_of_text|>", "<|start_header_id|>", "<|end_header_id|>", "*", "**", "`", "\"\"\""]
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        prefixes = ["assistant", "911 caller:", "Response:", "Caller:", "A:", "User:", "AI:", "The caller says:", "I would say:"]
        for prefix in prefixes:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        response = response.replace("assistant", "").strip()
        
        # Take only the first line to prevent rambling
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]
        
        # Remove quotes
        response = re.sub(r'^"+|"+$', '', response)
        
        # Remove stage directions early in the process
        response = self._remove_stage_directions(response)
        
        # Fix sentence fragments
        response = self._fix_sentence_fragments(response)
        
        # Fix grammar and punctuation
        response = self._fix_grammar_and_punctuation(response, emotional_state)
        
        # Ensure response isn't too short
        if len(response.split()) < 3 or not response.strip():
            response = self._generate_fallback_response(question, caller_state)
        
        # Remove parenthetical and bracketed content
        response = re.sub(r'\(.*?\)', '', response)
        response = re.sub(r'\[.*?\]', '', response)
        
        # Remove emotional indicators
        response = self._remove_emotional_indicators(response)
        
        # Make language more natural
        response = self._naturalize_language(response, emotional_state)
        
        # Fix poor grammar patterns
        response = self._fix_poor_grammar(response)
        
        # Validate response addresses the question
        if question and not self._validate_response_addresses_question(question, response):
            response = self._generate_direct_response(question, response, emotional_state)

        # Add conversational elements sparingly
        response = self._add_conversational_elements(response, emotional_state)
        
        # Fix hanging phrases
        response = self._fix_hanging_phrases(response)
        
        # Normalize punctuation
        response = self._normalize_punctuation(response, emotional_state)
        
        # Final coherence check
        response = self._ensure_coherent_response(response, question)
        
        return response.strip()

    def _remove_stage_directions(self, response: str) -> str:
        """Remove stage directions and action descriptions that don't belong in speech"""
        # Remove common stage directions
        stage_directions = [
            r'\bpauses?\b', r'\bpause\b', r'\blaughs?\b', r'\blaughter\b', 
            r'\bsighs?\b', r'\bcries?\b', r'\bsobbing\b', r'\bwhispers?\b',
            r'\bshouts?\b', r'\byells?\b', r'\bscreams?\b', r'\bmumbles?\b',
            r'\bstutters?\b', r'\bhesitates?\b', r'\bclears throat\b',
            r'\btakes a breath\b', r'\bbreathing heavily\b', r'\bsniffles?\b',
            r'\bvoice shaking\b', r'\bvoice trembling\b', r'\bin a shaky voice\b'
        ]
        
        for direction in stage_directions:
            response = re.sub(direction, '', response, flags=re.IGNORECASE)
        
        # Remove text in parentheses that contains stage directions
        response = re.sub(r'\([^)]*(?:pause|laugh|sigh|cry|whisper|shout|yell|scream|mumble|stutter|hesitate|breath|sniffle|shake|tremble)[^)]*\)', '', response, flags=re.IGNORECASE)
        
        # Clean up multiple spaces left by removals
        response = re.sub(r'\s+', ' ', response)
        
        return response.strip()

    def _generate_fallback_response(self, question: str, caller_state: CallerState) -> str:
        """Generate a fallback response when the original is too short or nonsensical"""
        if not question:
            return "I need help."
        
        question_lower = question.lower()
        
        if 'number' in question_lower or 'phone' in question_lower:
            context = caller_state.caller_profile.get('selected_context', {}) if caller_state else {}
            phone = context.get('phone', '587-555-0123')
            return f"It's {phone}."
        
        elif 'location' in question_lower or 'where' in question_lower:
            return "I'm not sure of the exact address."
        
        elif 'hurt' in question_lower or 'injured' in question_lower:
            return "I'm not sure."
        
        elif 'happened' in question_lower or 'what' in question_lower:
            return "There's been an accident."
        
        return "I'm not sure about that."

    def _ensure_coherent_response(self, response: str, question: str) -> str:
        """Final check to ensure the response makes sense and answers the question"""
        if not response or len(response.split()) < 2:
            return self._generate_fallback_response(question, None)
        
        # Remove nonsensical phrases
        nonsense_patterns = [
            r'\bthingamajig\b', r'\bwhatever\b', r'\banyway\b(?!\s+\w+)',
            r'\bwherever I\'m anyway\b', r'\bthat\'s where I\'m\. wherever I\'m\b',
            r'\bthis thingamajig has GPS on it\b'
        ]
        
        for pattern in nonsense_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up the response
        response = re.sub(r'\s+', ' ', response).strip()
        
        # If response became too short, provide a simple answer
        if len(response.split()) < 3:
            return self._generate_fallback_response(question, None)
        
        return response

    def _fix_sentence_fragments(self, response: str) -> str:
        # Fix common fragment patterns at the start
        response = re.sub(r'^\s*([A-Z])\.\s*([A-Z])', r'\1\2', response)
        response = re.sub(r'^\s*([A-Z][a-z]*)\.\s*([A-Z][a-z]*)', r'\1 \2', response)
        response = re.sub(r'^\s*([A-Z][a-z]*)\.\s+([A-Z][a-z]*)', r'\1 \2', response)
        response = re.sub(r'^([A-Z][a-z]*)\.\s*([A-Z][a-z]*)', r'\1 \2', response)
        response = re.sub(r'^\s*([A-Z][a-z]{1,3})\.\s*([A-Z])', r'\1 \2', response)
        
        # Fix fragments in the middle of sentences
        response = re.sub(r'\b([A-Z][a-z]{1,3})\.\s*([A-Z][a-z])', r'\1 \2', response)
        
        # Fix specific problematic patterns
        response = re.sub(r'\bIt\.\s*It\'s\b', "It's", response)
        response = re.sub(r'\bMy\.\s*Uh\.\s*', "My ", response)
        response = re.sub(r'\bWe\.\s*We\'re\b', "We're", response)
        
        return response.strip()

    def _fix_grammar_and_punctuation(self, response: str, emotional_state: EmotionalState = None) -> str:
        sentences = re.split(r'([.!?]+)', response)
        corrected_sentences = []
        
        for i, part in enumerate(sentences):
            if i % 2 == 0:
                part = part.strip()
                if part:
                    part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
                corrected_sentences.append(part)
            else:  
                corrected_sentences.append(part)
        
        response = ''.join(corrected_sentences)
        
        response = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', response)

        response = re.sub(r'\bi\b', 'I', response)
        
        return response
    
    def _normalize_punctuation(self, response: str, emotional_state: EmotionalState = None) -> str:
        response = re.sub(r'!+', '!', response)
        response = re.sub(r'!\s*!', '!', response)
        
        response = re.sub(r'\.\.\.+', '.', response)
        response = re.sub(r'\.\s*\.', '.', response)
        response = re.sub(r'\.\s+$', '.', response)
        
        response = re.sub(r'[!?]\.', '.', response)
        response = re.sub(r'\.!', '.', response)
        
        exclamation_pattern = r'!(?=\s+[A-Z]|\s*$)'
        
        if emotional_state in [EmotionalState.CALM, EmotionalState.WORRIED, EmotionalState.RELIEVED]:
            response = re.sub(exclamation_pattern, '.', response)
        elif emotional_state in [EmotionalState.PANICKED, EmotionalState.HYSTERICAL]:
            exclamation_count = len(re.findall(r'!', response))
            if exclamation_count > 2:
                matches = list(re.finditer(r'!', response))
                for i, match in enumerate(matches[2:], 2):
                    response = response[:match.start()] + '.' + response[match.end():]
        
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
    
    def _fix_hanging_phrases(self, response: str) -> str:
        hanging_patterns = [
            (r'\bit seems!$', '.'),
            (r'\bit seems\.$', '.'),
            (r'\bit looks!$', '.'),
            (r'\bit looks\.$', '.'),
            (r'\byou know!$', '.'),
            (r'\byou know\.$', '.'),
            (r'\bi guess!$', '.'),
            (r'\bi guess\.$', '.'),
            (r'\bi think!$', '.'),
            (r'\bi think\.$', '.'),
            (r'\bI mean!$', '.'),
            (r'\bI mean\.$', '.'),
            (r'\blike!$', '.'),
            (r'\blike\.$', '.'),
            (r'\bso!$', '.'),
            (r'\bso\.$', '.'),
            (r'\band!$', '.'),
            (r'\band\.$', '.'),
            (r'\bbut!$', '.'),
            (r'\bbut\.$', '.'),
            (r'\bor!$', '.'),
            (r'\bor\.$', '.'),
        ]
        
        for pattern, replacement in hanging_patterns:
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        hanging_words = ['seems', 'looks', 'thinks', 'guess', 'mean', 'like', 'so', 'and', 'but', 'or']
        words = response.split()
        if len(words) > 1 and words[-1].rstrip('!.').lower() in hanging_words:
            if words[-1].endswith(('!', '.')):
                words[-1] = words[-1][:-1] + '.'
            response = ' '.join(words)
        
        response = re.sub(r'\s+([.!?])', r'\1', response)
        
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
        
        return response
    
    def _fix_poor_grammar(self, response: str) -> str:
        grammar_fixes = {
            r'\bplz\b': 'please',
            r'\bu\b': 'you',
            r'\bur\b': 'your',
            r'\bcuz\b': 'because',
            r'\bya\b': 'you',
            r'\bem\b(?!\w)': 'them',
            r'\bn\b(?=\s)': 'and'
        }
        
        for incorrect, correct in grammar_fixes.items():
            response = re.sub(incorrect, correct, response, flags=re.IGNORECASE)
        
        response = re.sub(r'\bthey coulda\b', 'they could have', response, flags=re.IGNORECASE)
        response = re.sub(r'\bwoulda\b', 'would have', response, flags=re.IGNORECASE)
        response = re.sub(r'\bshoulda\b', 'should have', response, flags=re.IGNORECASE)
        
        return response
    
    def _add_conversational_elements(self, response: str, emotional_state: EmotionalState = None) -> str:
        if len(response.split()) < 4:
            return response

        starters = ["Um, ", "Well, ", "Okay, ", "So, ", "Right, "]
        fillers = [" like", " you know", " I mean", " I guess"]
        
        # Reduce probability of adding conversational elements to keep responses cleaner
        starter_prob = 0.02
        filler_prob = 0.01
        
        if emotional_state in [EmotionalState.PANICKED, EmotionalState.HYSTERICAL]:
            starter_prob = 0.05
            filler_prob = 0.02
            
        if random.random() < starter_prob and not response.startswith(("Um", "Well", "Okay", "So", "Right")):
            response = random.choice(starters) + response.lower()

        if random.random() < filler_prob:
            words = response.split()
            if len(words) > 5:  # Only add fillers to longer responses
                insert_pos = random.randint(2, len(words)-2)  # Avoid inserting too early or late
                safe_to_insert = True
                
                if insert_pos > 0:
                    prev_word = words[insert_pos-1]
                    if prev_word.endswith(('.', '!', '?')):
                        safe_to_insert = False
                
                if safe_to_insert:
                    words.insert(insert_pos, random.choice(fillers))
                    response = " ".join(words)
        
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
        
        if 'how many' in question_lower:
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
