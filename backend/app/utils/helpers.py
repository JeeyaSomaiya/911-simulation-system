import uuid
import logging
from datetime import datetime
from typing import Any, Dict

def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())

def log_event(event_type: str, data: Dict[Any, Any], level: str = 'info'):
    """Log an event with structured data"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data
    }
    
    if level == 'debug':
        logger.debug(f"Event: {event_type}", extra=log_data)
    elif level == 'warning':
        logger.warning(f"Event: {event_type}", extra=log_data)
    elif level == 'error':
        logger.error(f"Event: {event_type}", extra=log_data)
    else:
        logger.info(f"Event: {event_type}", extra=log_data)

def validate_audio_format(audio_data: bytes) -> bool:
    """Validate audio data format"""
    # Basic validation - should be expanded based on requirements
    return len(audio_data) > 0

def calculate_audio_duration(audio_data: bytes, sample_rate: int = 16000) -> float:
    """Calculate audio duration in seconds"""
    # Simplified calculation - assumes 16-bit mono audio
    samples = len(audio_data) // 2  # 16-bit = 2 bytes per sample
    return samples / sample_rate
