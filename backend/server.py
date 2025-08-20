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
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from flask import Flask, request, jsonify
from flask_cors import CORS
import redis

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

class EmotionalState(Enum):
    CALM = "calm"
    WORRIED = "worried"
    PANICKED = "panicked"
    HYSTERICAL = "hysterical"
    RELIEVED = "relieved"

class ScenarioType(Enum):
    TRAFFIC_ACCIDENT_10_01 = "10-01"
    TRAFFIC_ACCIDENT_10_02 = "10-02"
    MISC_INDUSTRIAL_10_03 = "10-03"
    ALARM_10_04 = "10-04"
    ALARM_VIDEO_10_04 = "10-04-video"
    ASSAULT_10_05 = "10-05"
    ASSISTANCE_10_06 = "10-06"
    SUICIDE_THREAT_10_07 = "10-07"
    BREAK_ENTER_10_08 = "10-08"
    HOME_INVASION_10_08H = "10-08H"
    HOME_INVASION_10_09 = "10-09"
    ANIMAL_10_10 = "10-10"
    DOMESTIC_10_11 = "10-11"
    DOMESTIC_STANDBY_10_11 = "10-11-standby"
    DRUNK_DISTURBANCE_10_12 = "10-12"
    ESCORT_10_13 = "10-13"
    DISTURBANCE_10_14 = "10-14"
    FIRE_10_15 = "10-15"
    FRAUD_10_16 = "10-16"
    INDECENT_ACT_10_17 = "10-17"
    LOST_FOUND_10_20 = "10-20"
    SUSPICIOUS_PACKAGE_10_20 = "10-20-package"
    EXPLOSIVE_10_20 = "10-20-explosive"
    MENTAL_HEALTH_10_21 = "10-21"
    MISSING_PERSON_10_22 = "10-22"
    NOISE_PARTY_10_24 = "10-24"
    ESCAPED_PRISONER_10_26 = "10-26"
    PROPERTY_DAMAGE_10_27 = "10-27"
    PRODUCT_CONTAMINATION_10_27 = "10-27-contamination"
    ROBBERY_10_30 = "10-30"
    SHOPLIFTING_10_31 = "10-31"
    SUDDEN_DEATH_10_32 = "10-32"
    SUSPICIOUS_PERSON_10_33 = "10-33"
    PANHANDLING_10_33 = "10-33-panhandling"
    THEFT_10_34 = "10-34"
    GAS_THEFT_10_34 = "10-34-gas"
    THREATS_10_35 = "10-35"
    SEXUAL_ASSAULT_10_36 = "10-36"
    MEDICAL_COLLAPSE_10_37 = "10-37"
    DRUGS_10_38 = "10-38"
    NOISE_EXCESSIVE_10_39 = "10-39"
    GUNSHOTS_10_40 = "10-40"
    UNWANTED_GUEST_10_41 = "10-41"
    HARASSMENT_10_42 = "10-42"
    WELFARE_CHECK_10_43 = "10-43"
    ABUSE_10_43 = "10-43-abuse"
    KEEP_PEACE_10_43 = "10-43-peace"
    IMMINENT_DANGER_10_43 = "10-43-danger"
    UNKNOWN_THIRD_PARTY_10_43 = "10-43-unknown"
    ABDUCTION_10_44 = "10-44"
    PARENTAL_ABDUCTION_10_44 = "10-44-parental"
    NOTIFICATION_10_45 = "10-45"
    CHILD_CUSTODY_10_47 = "10-47"
    WANTED_10_53 = "10-53"
    MENTAL_WARRANT_10_53 = "10-53-mental"
    UAL_WARRANT_10_53 = "10-53-ual"
    PROSTITUTION_10_69 = "10-69"
    ABANDONED_AUTO_10_81 = "10-81"
    CARELESS_DRIVER_10_82 = "10-82"
    ROAD_RAGE_10_82 = "10-82-rage"
    IMPAIRED_DRIVER_10_83 = "10-83"
    HIT_AND_RUN_10_84 = "10-84"
    SPEEDER_10_85 = "10-85"
    STOLEN_AUTO_10_86 = "10-86"
    RECOVERED_AUTO_10_86 = "10-86-recovered"
    SUSPICIOUS_VEHICLE_10_87 = "10-87"
    TRAFFIC_HAZARD_10_88 = "10-88"
    HAZMAT_SPILL_10_91 = "10-91"
    AIRCRAFT_INCIDENT_10_92 = "10-92"
    ACT_OF_NATURE_10_93 = "10-93"
    LURING_10_97 = "10-97"
    MISCELLANEOUS_X99 = "X99"
    BANK_HOLDUP_100 = "100"
    OFFICER_TROUBLE_200 = "200"
    FIREARM_300 = "300"
    SHOTS_FIRED_300 = "300-shots"
    HOSTAGE_300 = "300-hostage"
    SHOOTING_VICTIM_300 = "300-victim"
    ACTIVE_ASSAILANT_300 = "300-assailant"
    BOMB_THREAT_400 = "400"
    EXPLOSIVE_FOUND_400 = "400-found"
    EXPLOSION_400 = "400-explosion"
    EXTORTION_500 = "500"
    AIRCRAFT_HIJACK_800 = "800"
    PUBLIC_SAFETY_1000 = "1000"
    MAJOR_INCIDENT_2000 = "2000"
    PRISON_RIOT_5000 = "5000"
    PRISON_BLUE_5000 = "5000-blue"

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

class HuggingFaceCallerGenerator:
    def __init__(self):
        self.model_path = "/home/ubuntu/.llama/checkpoints/Llama3.1-8B-Instruct-hf"
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.scenario_contexts = self._load_scenario_contexts()
        self.lock = Lock()
        self.load_model()
        logger.info("Hugging Face Llama-3.1-8B Caller Generator initialized")
    
    def _load_scenario_contexts(self):
        return {
            ScenarioType.TRAFFIC_ACCIDENT_10_01: {
                "location": "Cranston Ave SE / Deerfoot Tr SE",
                "caller_name": "Broderick Greene", 
                "phone": "403-561-9988",
                "situation": "Witnessed a rollover accident. White SUV is currently in the ditch off southbound Deerfoot Trail just south of Cranston Ave SE. Vehicle appears to have rolled over due to black ice conditions.",
                "current_status": "Drive-by caller who has already left the scene. Observed the accident about 1 minute ago. Driver appears to be injured and trapped in the overturned vehicle.",
                "caller_background": "Excited drive-by caller who witnessed the accident while driving. Not at scene anymore but concerned about the driver's safety.",
                "initial_response": "There's been a bad accident!"
            },
            ScenarioType.TRAFFIC_ACCIDENT_10_02: {
                "location": "10 AV SW / 16 ST SW",
                "caller_name": "Candy Wise", 
                "phone": "587-543-6789",
                "situation": "Non-injury accident - one vehicle rear ended another at intersection. Both vehicles still drivable.",
                "current_status": "Drivers are exchanging information. Traffic backing up but no injuries reported.",
                "caller_background": "Witness who saw the accident but didn't stop. Vague about location details.",
                "initial_response": "I just saw a car accident!"
            },
            ScenarioType.ROBBERY_10_30: {
                "location": "South Centre Mall, 100 Anderson Rd SE",
                "caller_name": "Tony Hilson", 
                "phone": "403-665-8532",
                "situation": "Just found a male bleeding outside Safeway; says he was stabbed and robbed of his wallet and phone.",
                "current_status": "Victim is conscious but bleeding from his arm. Suspect described as white male, 25yrs old, 6', slim build, wearing white baseball cap, green hoody, blue jeans. Last seen running towards Anderson Rd through mall parking lot.",
                "caller_background": "Bystander who found the victim. Upset but trying to help. Applying pressure to wound while on call.",
                "initial_response": "I found someone bleeding!"
            },
            ScenarioType.HOME_INVASION_10_08H: {
                "location": "33 Brightondale Pr SE",
                "caller_name": "Tony Hernandez", 
                "phone": "403-483-4384",
                "situation": "Two men kicked down the door and invaded home. Used bear spray and knife. Stole laptop.",
                "current_status": "Caller hiding in bedroom. Intruders just left but might return. Caller's eyes burning from bear spray. Home trashed.",
                "caller_background": "Homeowner terrified for safety. Hiding and afraid intruders might come back.",
                "initial_response": "Intruders broke into my home!"
            },
            ScenarioType.IMPAIRED_DRIVER_10_83: {
                "location": "Stoney Trail/Country Hills BV",
                "caller_name": "Betty Jensen", 
                "phone": "403-562-1159",
                "situation": "Observing vehicle swerving erratically, hitting brakes randomly, unable to stay in lanes.",
                "current_status": "Following vehicle eastbound on Stoney Trail. Driver appears impaired. Red VW Golf, license BJR5561.",
                "caller_background": "Concerned driver returning from Banff to Airdrie. Insistent on following vehicle despite safety concerns.",
                "initial_response": "I'm seeing a dangerous driver!"
            },
            ScenarioType.GAS_THEFT_10_34: {
                "location": "7-11 Woodbine, 460 Woodbine BV SW",
                "caller_name": "Janine Shotbothsides", 
                "phone": "403-250-2374",
                "situation": "Vehicle drove off without paying for $82.39 worth of gas.",
                "current_status": "Red pickup truck with license BPT5789 fled scene turning right toward 24 St. Driver: WM, late 20s, baseball cap, grey winter jacket.",
                "caller_background": "Gas station employee reporting theft. Calm but wants police intervention.",
                "initial_response": "Someone stole gas!"
            },
            ScenarioType.MENTAL_HEALTH_10_21: {
                "location": "N/A - Caller won't provide location",
                "caller_name": "Selena Crock", 
                "phone": "403-271-8645",
                "situation": "Caller reporting feeling watched during shopping trip and noticing suspicious number of red cars.",
                "current_status": "Caller is safe but paranoid. Rambling about people looking at her and red cars being suspicious.",
                "caller_background": "Individual experiencing paranoid thoughts. Refuses to provide location but wants police awareness.",
                "initial_response": "People are acting suspiciously!"
            },
            ScenarioType.SUICIDE_THREAT_10_07: {
                "location": "Unknown",
                "caller_name": "Beth Hunter", 
                "phone": "403-266-4357",
                "situation": "Male caller to distress center threatened to take pills after recent breakup.",
                "current_status": "Caller hung up when told police would be contacted. Identity: Dan Depta, possibly middle-aged, might be drinking.",
                "caller_background": "Distress center employee reporting third-party suicide threat. Cooperative but lacks location information.",
                "initial_response": "A man threatened to kill himself!"
            },
            ScenarioType.TRAFFIC_HAZARD_10_88: {
                "location": "Northbound Deerfoot at 16 Av",
                "caller_name": "Candy Wise", 
                "phone": "403-555-0123",
                "situation": "Car stopped on side of Deerfoot with person inside.",
                "current_status": "Dark SUV parked on shoulder. Driver appears to be a white male in green jacket.",
                "caller_background": "Drive-by caller reporting traffic hazard. Not stopping but concerned about stopped vehicle.",
                "initial_response": "I saw a car stopped on the road!"
            },
            ScenarioType.THEFT_10_34: {
                "location": "705 8 ST SW",
                "caller_name": "Jamal Samsonoff", 
                "phone": "825-834-4672",
                "situation": "Theft from convenience store - suspect grabbed chips and pop and ran away.",
                "current_status": "Suspect ran toward LRT station eastbound. White male, 20-25, 6'0, heavy build, blue shirt, jeans, red shoes.",
                "caller_background": "Store employee reporting theft, upset and wanting immediate police response.",
                "initial_response": "We've been robbed!"
            }
        }
    
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

generator = HuggingFaceCallerGenerator()

sessions = {}

class SessionManager:
    def create_session(self, trainee_id: str, scenario_type: str) -> SessionData:
        session_id = str(uuid.uuid4())
        scenario_map = {
            "10-01": ScenarioType.TRAFFIC_ACCIDENT_10_01,
            "10-02": ScenarioType.TRAFFIC_ACCIDENT_10_02,
            "10-03": ScenarioType.MISC_INDUSTRIAL_10_03,
            "10-04": ScenarioType.ALARM_10_04,
            "10-04-video": ScenarioType.ALARM_VIDEO_10_04,
            "10-05": ScenarioType.ASSAULT_10_05,
            "10-06": ScenarioType.ASSISTANCE_10_06,
            "10-07": ScenarioType.SUICIDE_THREAT_10_07,
            "10-08": ScenarioType.BREAK_ENTER_10_08,
            "10-08H": ScenarioType.HOME_INVASION_10_08H,
            "10-09": ScenarioType.HOME_INVASION_10_09,
            "10-10": ScenarioType.ANIMAL_10_10,
            "10-11": ScenarioType.DOMESTIC_10_11,
            "10-11-standby": ScenarioType.DOMESTIC_STANDBY_10_11,
            "10-12": ScenarioType.DRUNK_DISTURBANCE_10_12,
            "10-13": ScenarioType.ESCORT_10_13,
            "10-14": ScenarioType.DISTURBANCE_10_14,
            "10-15": ScenarioType.FIRE_10_15,
            "10-16": ScenarioType.FRAUD_10_16,
            "10-17": ScenarioType.INDECENT_ACT_10_17,
            "10-20": ScenarioType.LOST_FOUND_10_20,
            "10-20-package": ScenarioType.SUSPICIOUS_PACKAGE_10_20,
            "10-20-explosive": ScenarioType.EXPLOSIVE_10_20,
            "10-21": ScenarioType.MENTAL_HEALTH_10_21,
            "10-22": ScenarioType.MISSING_PERSON_10_22,
            "10-24": ScenarioType.NOISE_PARTY_10_24,
            "10-26": ScenarioType.ESCAPED_PRISONER_10_26,
            "10-27": ScenarioType.PROPERTY_DAMAGE_10_27,
            "10-27-contamination": ScenarioType.PRODUCT_CONTAMINATION_10_27,
            "10-30": ScenarioType.ROBBERY_10_30,
            "10-31": ScenarioType.SHOPLIFTING_10_31,
            "10-32": ScenarioType.SUDDEN_DEATH_10_32,
            "10-33": ScenarioType.SUSPICIOUS_PERSON_10_33,
            "10-33-panhandling": ScenarioType.PANHANDLING_10_33,
            "10-34": ScenarioType.THEFT_10_34,
            "10-35": ScenarioType.THREATS_10_35,
            "10-36": ScenarioType.SEXUAL_ASSAULT_10_36,
            "10-37": ScenarioType.MEDICAL_COLLAPSE_10_37,
            "10-38": ScenarioType.DRUGS_10_38,
            "10-39": ScenarioType.NOISE_EXCESSIVE_10_39,
            "10-40": ScenarioType.GUNSHOTS_10_40,
            "10-41": ScenarioType.UNWANTED_GUEST_10_41,
            "10-42": ScenarioType.HARASSMENT_10_42,
            "10-43": ScenarioType.WELFARE_CHECK_10_43,
            "10-43-abuse": ScenarioType.ABUSE_10_43,
            "10-43-peace": ScenarioType.KEEP_PEACE_10_43,
            "10-43-danger": ScenarioType.IMMINENT_DANGER_10_43,
            "10-43-unknown": ScenarioType.UNKNOWN_THIRD_PARTY_10_43,
            "10-44": ScenarioType.ABDUCTION_10_44,
            "10-44-parental": ScenarioType.PARENTAL_ABDUCTION_10_44,
            "10-45": ScenarioType.NOTIFICATION_10_45,
            "10-47": ScenarioType.CHILD_CUSTODY_10_47,
            "10-53": ScenarioType.WANTED_10_53,
            "10-53-mental": ScenarioType.MENTAL_WARRANT_10_53,
            "10-53-ual": ScenarioType.UAL_WARRANT_10_53,
            "10-69": ScenarioType.PROSTITUTION_10_69,
            "10-81": ScenarioType.ABANDONED_AUTO_10_81,
            "10-82": ScenarioType.CARELESS_DRIVER_10_82,
            "10-82-rage": ScenarioType.ROAD_RAGE_10_82,
            "10-83": ScenarioType.IMPAIRED_DRIVER_10_83,
            "10-84": ScenarioType.HIT_AND_RUN_10_84,
            "10-85": ScenarioType.SPEEDER_10_85,
            "10-86": ScenarioType.STOLEN_AUTO_10_86,
            "10-86-recovered": ScenarioType.RECOVERED_AUTO_10_86,
            "10-87": ScenarioType.SUSPICIOUS_VEHICLE_10_87,
            "10-88": ScenarioType.TRAFFIC_HAZARD_10_88,
            "10-91": ScenarioType.HAZMAT_SPILL_10_91,
            "10-92": ScenarioType.AIRCRAFT_INCIDENT_10_92,
            "10-93": ScenarioType.ACT_OF_NATURE_10_93,
            "10-97": ScenarioType.LURING_10_97,
            "X99": ScenarioType.MISCELLANEOUS_X99,
            "100": ScenarioType.BANK_HOLDUP_100,
            "200": ScenarioType.OFFICER_TROUBLE_200,
            "300": ScenarioType.FIREARM_300,
            "300-shots": ScenarioType.SHOTS_FIRED_300,
            "300-hostage": ScenarioType.HOSTAGE_300,
            "300-victim": ScenarioType.SHOOTING_VICTIM_300,
            "300-assailant": ScenarioType.ACTIVE_ASSAILANT_300,
            "400": ScenarioType.BOMB_THREAT_400,
            "400-found": ScenarioType.EXPLOSIVE_FOUND_400,
            "400-explosion": ScenarioType.EXPLOSION_400,
            "500": ScenarioType.EXTORTION_500,
            "800": ScenarioType.AIRCRAFT_HIJACK_800,
            "1000": ScenarioType.PUBLIC_SAFETY_1000,
            "2000": ScenarioType.MAJOR_INCIDENT_2000,
            "5000": ScenarioType.PRISON_RIOT_5000,
            "5000-blue": ScenarioType.PRISON_BLUE_5000,
            "10-34-gas": ScenarioType.GAS_THEFT_10_34,
            "10-30-stab": ScenarioType.ROBBERY_10_30
        }
        
        scenario_enum = scenario_map.get(scenario_type, ScenarioType.TRAFFIC_ACCIDENT_10_01)
        
        initial_intensity = 9 if scenario_enum in [
            ScenarioType.ROBBERY_10_30, 
            ScenarioType.HOME_INVASION_10_08H,
            ScenarioType.HOME_INVASION_10_09,
            ScenarioType.BREAK_ENTER_10_08,
            ScenarioType.ASSAULT_10_05,
            ScenarioType.SEXUAL_ASSAULT_10_36,
            ScenarioType.GUNSHOTS_10_40,
            ScenarioType.FIREARM_300,
            ScenarioType.SHOTS_FIRED_300,
            ScenarioType.HOSTAGE_300,
            ScenarioType.SHOOTING_VICTIM_300,
            ScenarioType.ACTIVE_ASSAILANT_300,
            ScenarioType.BANK_HOLDUP_100,
            ScenarioType.OFFICER_TROUBLE_200,
            ScenarioType.ABDUCTION_10_44,
            ScenarioType.PARENTAL_ABDUCTION_10_44,
            ScenarioType.SUICIDE_THREAT_10_07,
            ScenarioType.BOMB_THREAT_400,
            ScenarioType.EXPLOSIVE_FOUND_400,
            ScenarioType.EXPLOSION_400
        ] else 7
        initial_emotion = EmotionalState.PANICKED if initial_intensity > 7 else EmotionalState.WORRIED
        
        initial_state = CallerState(
            emotional_state=initial_emotion,
            intensity=initial_intensity,
            scenario_type=scenario_enum,
            key_details_revealed=[],
            conversation_history=[],
            caller_profile={"scenario": scenario_type},
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

@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        trainee_id = data.get('trainee_id', 'default')
        scenario_type = data.get('scenario_type', '10-01')
        
        session = session_manager.create_session(trainee_id, scenario_type)
        initial_message = generator.generate_initial_response(session.scenario_type)
        
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
        debug=True
    )
