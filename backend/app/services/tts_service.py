import logging
import asyncio
from typing import Dict, Any, Optional
import numpy as np
from TTS.api import TTS
import tempfile
import os
import threading
import queue

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.tts_model = None
        self.active_sessions = {}
        self.audio_queue = queue.Queue()
        
        # Emotional voice configurations
        self.voice_configs = {
            'CALM': {
                'speed': 1.0,
                'pitch': 0.0,
                'volume': 0.8,
                'emotion': 'neutral'
            },
            'WORRIED': {
                'speed': 1.1,
                'pitch': 0.1,
                'volume': 0.9,
                'emotion': 'concerned'
            },
            'PANICKED': {
                'speed': 1.3,
                'pitch': 0.3,
                'volume': 1.0,
                'emotion': 'stressed'
            },
            'HYSTERICAL': {
                'speed': 1.5,
                'pitch': 0.5,
                'volume': 1.0,
                'emotion': 'crying'
            },
            'RELIEVED': {
                'speed': 0.9,
                'pitch': -0.1,
                'volume': 0.7,
                'emotion': 'happy'
            }
        }
    
    def initialize(self):
        """Initialize TTS model"""
        try:
            # Initialize Coqui TTS
            self.tts_model = TTS(
                model_name="tts_models/en/ljspeech/tacotron2-DDC",
                gpu=self.use_gpu
            )
            
            logger.info("TTS service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            raise
    
    def generate_speech(self, session_id: str, text: str, 
                       emotional_state: str = 'CALM', 
                       intensity: int = 5) -> Dict[str, Any]:
        """Generate speech audio from text"""
        try:
            if not self.tts_model:
                self.initialize()
            
            # Get voice configuration for emotional state
            voice_config = self.voice_configs.get(emotional_state, self.voice_configs['CALM'])
            
            # Adjust parameters based on intensity
            adjusted_speed = voice_config['speed'] + (intensity - 5) * 0.05
            adjusted_pitch = voice_config['pitch'] + (intensity - 5) * 0.02
            adjusted_volume = min(1.0, voice_config['volume'] + (intensity - 5) * 0.02)
            
            # Apply emotional modifications to text
            modified_text = self._apply_emotional_modifications(text, emotional_state, intensity)
            
            # Generate audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            self.tts_model.tts_to_file(
                text=modified_text,
                file_path=temp_path
            )
            
            # Read generated audio
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Apply audio effects based on emotional state
            processed_audio = self._apply_audio_effects(
                audio_data, emotional_state, intensity
            )
            
            return {
                'session_id': session_id,
                'audio_data': processed_audio,
                'text': text,
                'emotional_state': emotional_state,
                'intensity': intensity,
                'audio_format': 'wav',
                'sample_rate': 22050,
                'channels': 1,
                'generated_at': 'timestamp'
            }
            
        except Exception as e:
            logger.error(f"Error generating speech for session {session_id}: {e}")
            return {
                'session_id': session_id,
                'error': str(e),
                'text': text
            }
    
    def _apply_emotional_modifications(self, text: str, emotional_state: str, 
                                     intensity: int) -> str:
        """Apply emotional modifications to text"""
        if emotional_state == 'PANICKED' and intensity > 6:
            # Add stuttering and repetition for panic
            words = text.split()
            if len(words) > 0:
                # Stutter on first word occasionally
                if np.random.random() < 0.3:
                    first_word = words[0]
                    if len(first_word) > 1:
                        words[0] = f"{first_word[0]}-{first_word}"
                
                # Add filler words
                if np.random.random() < 0.4:
                    filler_words = ['um', 'uh', 'like']
                    filler = np.random.choice(filler_words)
                    insert_pos = min(2, len(words))
                    words.insert(insert_pos, filler)
            
            text = ' '.join(words)
        
        elif emotional_state == 'HYSTERICAL':
            # Add emotional exclamations
            exclamations = ['Oh God', 'Please', 'Help me']
            if np.random.random() < 0.5:
                text = f"{np.random.choice(exclamations)}! {text}"
        
        elif emotional_state == 'CALM':
            # Remove excessive punctuation
            text = text.replace('!!', '.').replace('!', '.')
        
        return text
    
    def _apply_audio_effects(self, audio_data: bytes, emotional_state: str, 
                           intensity: int) -> bytes:
        """Apply audio effects based on emotional state"""
        try:
            # Convert bytes to numpy array (simplified - would need proper audio processing)
            # This is a placeholder - in production you'd use librosa or similar
            
            # For now, just return original audio
            # In production, apply:
            # - Pitch shifting for emotional states
            # - Tremolo for nervous/scared states  
            # - Reverb for distance effects
            # - Noise for phone quality simulation
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error applying audio effects: {e}")
            return audio_data
    
    def get_audio_stream(self, session_id: str) -> Optional[bytes]:
        """Get next audio chunk for streaming"""
        try:
            if not self.audio_queue.empty():
                return self.audio_queue.get_nowait()
            return None
        except Exception as e:
            logger.error(f"Error getting audio stream: {e}")
            return None

# Global service instance
tts_service = TTSService(True)
