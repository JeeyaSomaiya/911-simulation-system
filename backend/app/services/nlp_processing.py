import logging
import spacy
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class NLPProcessingService:
    def __init__(self):
        self.nlp = None
        self.emergency_keywords = {
            'medical': [
                'heart attack', 'chest pain', 'bleeding', 'unconscious', 'breathing',
                'overdose', 'stroke', 'seizure', 'allergic reaction', 'broken bone',
                'burn', 'poisoning', 'pregnant', 'labor', 'diabetic', 'asthma'
            ],
            'fire': [
                'fire', 'smoke', 'burning', 'explosion', 'gas leak', 'flames',
                'house fire', 'apartment fire', 'car fire', 'wildfire'
            ],
            'police': [
                'robbery', 'burglary', 'assault', 'domestic violence', 'shooting',
                'stabbing', 'rape', 'kidnapping', 'drunk driver', 'theft',
                'vandalism', 'suspicious person', 'break in', 'weapon'
            ]
        }
        
        self.urgency_indicators = {
            'high': [
                'help', 'emergency', 'urgent', 'now', 'dying', 'blood', 'gun',
                'knife', 'fire', 'can\'t breathe', 'unconscious', 'overdose'
            ],
            'medium': [
                'hurt', 'injured', 'accident', 'sick', 'pain', 'problem'
            ],
            'low': [
                'report', 'complaint', 'question', 'information'
            ]
        }
        
        self.emotion_patterns = {
            'panicked': [
                r'\b(help|please|oh god|oh my god)\b', r'[!]{2,}', r'[A-Z]{3,}'
            ],
            'calm': [
                r'\b(thank you|okay|alright|understand)\b'
            ],
            'confused': [
                r'\b(what|where|how|why|don\'t know|not sure)\b'
            ],
            'angry': [
                r'\b(damn|hell|stupid|idiot)\b'
            ]
        }
        
    def initialize(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("NLP service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NLP service: {e}")
            raise
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities from text"""
        if not self.nlp:
            self.initialize()
            
        doc = self.nlp(text)
        entities = {
            'locations': [],
            'persons': [],
            'organizations': [],
            'dates': [],
            'numbers': [],
            'medical_conditions': [],
            'weapons': [],
            'vehicles': [],
            'injuries': []
        }
        
        # Extract standard NER entities
        for ent in doc.ents:
            entity_info = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # spaCy doesn't provide confidence scores
            }
            
            if ent.label_ in ['GPE', 'LOC', 'FAC']:
                entities['locations'].append(entity_info)
            elif ent.label_ == 'PERSON':
                entities['persons'].append(entity_info)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(entity_info)
            elif ent.label_ in ['DATE', 'TIME']:
                entities['dates'].append(entity_info)
            elif ent.label_ in ['CARDINAL', 'ORDINAL', 'QUANTITY']:
                entities['numbers'].append(entity_info)
        
        # Extract domain-specific entities
        entities.update(self._extract_emergency_entities(text))
        
        return entities
    
    def _extract_emergency_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract emergency-specific entities"""
        entities = {
            'medical_conditions': [],
            'weapons': [],
            'vehicles': [],
            'injuries': []
        }
        
        text_lower = text.lower()
        
        # Medical conditions
        medical_patterns = [
            r'\b(heart attack|chest pain|stroke|seizure|overdose)\b',
            r'\b(asthma|diabetes|allergic reaction)\b',
            r'\b(unconscious|not breathing|bleeding)\b'
        ]
        
        for pattern in medical_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                entities['medical_conditions'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        
        # Weapons
        weapon_patterns = [
            r'\b(gun|pistol|rifle|shotgun|firearm)\b',
            r'\b(knife|blade|machete|sword)\b',
            r'\b(bat|club|pipe|brick)\b'
        ]
        
        for pattern in weapon_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                entities['weapons'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        
        # Vehicles (simple patterns)
        vehicle_patterns = [
            r'\b(car|truck|van|suv|motorcycle|bike)\b',
            r'\b(sedan|coupe|pickup|minivan)\b'
        ]
        
        for pattern in vehicle_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                entities['vehicles'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8
                })
        
        return entities
    
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify the intent of the text"""
        text_lower = text.lower()
        
        # Determine emergency type
        emergency_scores = {}
        for emergency_type, keywords in self.emergency_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emergency_scores[emergency_type] = score
        
        # Get the emergency type with highest score
        emergency_type = max(emergency_scores.items(), key=lambda x: x[1])
        
        # Determine urgency level
        urgency_scores = {}
        for urgency_level, indicators in self.urgency_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            urgency_scores[urgency_level] = score
        
        urgency_level = max(urgency_scores.items(), key=lambda x: x[1])
        
        # Detect emotional state
        emotion_scores = {}
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            emotion_scores[emotion] = score
        
        detected_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        return {
            'emergency_type': emergency_type[0] if emergency_type[1] > 0 else 'unknown',
            'emergency_confidence': min(emergency_type[1] / 3.0, 1.0),
            'urgency_level': urgency_level[0] if urgency_level[1] > 0 else 'medium',
            'urgency_confidence': min(urgency_level[1] / 2.0, 1.0),
            'emotional_state': detected_emotion[0] if detected_emotion[1] > 0 else 'neutral',
            'emotion_confidence': min(detected_emotion[1] / 2.0, 1.0),
            'processing_timestamp': datetime.utcnow().isoformat()
        }
    
    def process_transcript_chunk(self, text: str, session_id: str) -> Dict[str, Any]:
        """Process a chunk of transcript text"""
        try:
            # Extract entities
            entities = self.extract_entities(text)
            
            # Classify intent
            intent = self.classify_intent(text)
            
            # Calculate confidence score
            overall_confidence = (
                intent['emergency_confidence'] + 
                intent['urgency_confidence'] + 
                intent['emotion_confidence']
            ) / 3.0
            
            return {
                'session_id': session_id,
                'text': text,
                'entities': entities,
                'intent': intent,
                'confidence': overall_confidence,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing transcript chunk: {e}")
            return {
                'session_id': session_id,
                'text': text,
                'entities': {},
                'intent': {'emergency_type': 'unknown', 'urgency_level': 'medium'},
                'confidence': 0.0,
                'error': str(e)
            }

# Global service instance
nlp_service = NLPProcessingService()
