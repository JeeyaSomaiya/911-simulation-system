import asyncio
import logging
import numpy as np
import librosa
import webrtcvad
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
from azure.cognitiveservices.speech.audio import AudioStreamFormat, PushAudioInputStream
from typing import AsyncGenerator, Optional
import threading
import queue
import time

logger = logging.getLogger(__name__)

class AudioProcessingService:
    def __init__(self, azure_speech_key: str, azure_speech_region: str):
        self.azure_speech_key = azure_speech_key
        self.azure_speech_region = azure_speech_region
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.active_sessions = {}
        
    def initialize_speech_recognizer(self, session_id: str) -> SpeechRecognizer:
        """Initialize Azure Speech Services recognizer for a session"""
        try:
            speech_config = SpeechConfig(
                subscription=self.azure_speech_key, 
                region=self.azure_speech_region
            )
            speech_config.speech_recognition_language = "en-US"
            speech_config.enable_dictation()
            
            # Create push stream
            stream_format = AudioStreamFormat(samples_per_second=self.sample_rate)
            audio_stream = PushAudioInputStream(stream_format)
            audio_config = AudioConfig(stream=audio_stream)
            
            recognizer = SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            self.active_sessions[session_id] = {
                'recognizer': recognizer,
                'audio_stream': audio_stream,
                'transcript_queue': queue.Queue(),
                'is_active': True
            }
            
            # Set up event handlers
            def on_recognized(evt):
                if evt.result.text.strip():
                    self.active_sessions[session_id]['transcript_queue'].put({
                        'text': evt.result.text,
                        'confidence': evt.result.confidence,
                        'timestamp': time.time()
                    })
            
            recognizer.recognized.connect(on_recognized)
            
            # Start continuous recognition
            recognizer.start_continuous_recognition()
            
            logger.info(f"Speech recognizer initialized for session: {session_id}")
            return recognizer
            
        except Exception as e:
            logger.error(f"Failed to initialize speech recognizer: {e}")
            raise
    
    def process_audio_chunk(self, session_id: str, audio_data: bytes) -> Optional[dict]:
        """Process a chunk of audio data"""
        try:
            if session_id not in self.active_sessions:
                self.initialize_speech_recognizer(session_id)
            
            session = self.active_sessions[session_id]
            
            # Voice Activity Detection
            is_speech = self.detect_speech(audio_data)
            
            if is_speech:
                # Send audio to Azure Speech Services
                session['audio_stream'].write(audio_data)
                
                # Check for new transcripts
                if not session['transcript_queue'].empty():
                    return session['transcript_queue'].get_nowait()
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk for session {session_id}: {e}")
            return None
    
    def detect_speech(self, audio_data: bytes) -> bool:
        """Detect speech using WebRTC VAD"""
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # WebRTC VAD requires specific frame sizes (10, 20, or 30ms)
            frame_duration_ms = 30
            frame_size = int(self.sample_rate * frame_duration_ms / 1000)
            
            # Process in chunks
            for i in range(0, len(audio_np), frame_size):
                frame = audio_np[i:i+frame_size]
                if len(frame) == frame_size:
                    frame_bytes = frame.tobytes()
                    if self.vad.is_speech(frame_bytes, self.sample_rate):
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return True  # Default to treating as speech if VAD fails
    
    def apply_noise_reduction(self, audio_data: bytes) -> bytes:
        """Apply noise reduction to audio data"""
        try:
            # Convert to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_np.astype(np.float32) / 32768.0
            
            # Simple noise reduction using spectral subtraction
            # In production, use more sophisticated methods
            stft = librosa.stft(audio_float)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise spectrum from first few frames
            noise_spectrum = np.mean(magnitude[:, :10], axis=1, keepdims=True)
            
            # Spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            enhanced_magnitude = magnitude - alpha * noise_spectrum
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft)
            
            # Convert back to int16
            enhanced_audio = (enhanced_audio * 32768.0).astype(np.int16)
            return enhanced_audio.tobytes()
            
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return audio_data  # Return original if processing fails
    
    def close_session(self, session_id: str):
        """Close audio processing session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['is_active'] = False
            session['recognizer'].stop_continuous_recognition()
            session['audio_stream'].close()
            del self.active_sessions[session_id]
            logger.info(f"Audio session closed: {session_id}")

# Global service instance
audio_service = AudioProcessingService("", "")  # Will be initialized with proper config
