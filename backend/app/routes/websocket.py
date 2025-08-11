from flask import Blueprint
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio
from app.services import (
    audio_service, nlp_service, llm_service, tts_service,
    analytics_service, session_service
)
from app.utils.event_bus import event_bus
from app.utils.helpers import log_event
import logging
import base64

websocket_bp = Blueprint('websocket', __name__)
logger = logging.getLogger(__name__)

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connected', {'status': 'Connected to AI 911 Training System'})

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")

@socketio.on('join_session')
def on_join_session(data):
    """Join a training session room"""
    try:
        session_id = data.get('session_id')
        if not session_id:
            emit('error', {'message': 'Missing session_id'})
            return
        
        # Verify session exists
        session_data = session_service.get_session(session_id)
        if not session_data:
            emit('error', {'message': 'Session not found'})
            return
        
        join_room(session_id)
        emit('joined_session', {
            'session_id': session_id,
            'scenario_type': session_data.get('scenario_type')
        })
        
        log_event('session_joined', {'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error joining session: {e}")
        emit('error', {'message': str(e)})

@socketio.on('leave_session')
def on_leave_session(data):
    """Leave a training session room"""
    try:
        session_id = data.get('session_id')
        if session_id:
            leave_room(session_id)
            emit('left_session', {'session_id': session_id})
            
    except Exception as e:
        logger.error(f"Error leaving session: {e}")
        emit('error', {'message': str(e)})

@socketio.on('audio_chunk')
def on_audio_chunk(data):
    """Handle incoming audio chunk"""
    try:
        session_id = data.get('session_id')
        audio_data = data.get('audio_data')
        
        if not session_id or not audio_data:
            emit('error', {'message': 'Missing session_id or audio_data'})
            return
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Process audio chunk
        transcript_result = audio_service.process_audio_chunk(session_id, audio_bytes)
        
        if transcript_result:
            # Emit transcript to client
            emit('transcript', {
                'session_id': session_id,
                'text': transcript_result['text'],
                'confidence': transcript_result['confidence'],
                'timestamp': transcript_result['timestamp']
            }, room=session_id)
            
            # Process with NLP
            nlp_result = nlp_service.process_transcript_chunk(
                transcript_result['text'], 
                session_id
            )
            
            # Publish events
            event_bus.publish_event(
                'audio.transcribed',
                nlp_result,
                session_id=session_id,
                source_service='audio_processing'
            )
            
            # Update analytics
            analytics_service.update_session_metrics(session_id, {
                'event_type': 'audio.transcribed',
                'payload': nlp_result
            })
            
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        emit('error', {'message': str(e)})

@socketio.on('call_taker_message')
def on_call_taker_message(data):
    """Handle call taker message"""
    try:
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            emit('error', {'message': 'Missing session_id or message'})
            return
        
        # Process with NLP
        nlp_result = nlp_service.process_transcript_chunk(message, session_id)
        
        # Generate caller response using LLM
        llm_response = llm_service.generate_response(
            session_id=session_id,
            call_taker_input=message,
            context=nlp_result
        )
        
        if 'error' not in llm_response:
            # Generate speech audio
            tts_result = tts_service.generate_speech(
                session_id=session_id,
                text=llm_response['response'],
                emotional_state=llm_response['emotional_state'],
                intensity=llm_response['intensity']
            )
            
            # Emit caller response
            emit('caller_response', {
                'session_id': session_id,
                'text': llm_response['response'],
                'emotional_state': llm_response['emotional_state'],
                'intensity': llm_response['intensity'],
                'audio_data': base64.b64encode(tts_result.get('audio_data', b'')).decode('utf-8') if 'audio_data' in tts_result else None
            }, room=session_id)
            
            # Publish events
            event_bus.publish_event(
                'llm.response_generated',
                llm_response,
                session_id=session_id,
                source_service='llm_orchestration'
            )
            
            # Update analytics
            analytics_service.update_session_metrics(session_id, {
                'event_type': 'llm.response_generated',
                'payload': llm_response
            })
            
            # Add to session timeline
            session_service.add_call_event(session_id, 'call_taker_message', {
                'message': message,
                'caller_response': llm_response['response'],
                'emotional_state': llm_response['emotional_state']
            })
        
        else:
            emit('error', {'message': llm_response['error']})
            
    except Exception as e:
        logger.error(f"Error processing call taker message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('request_score_update')
def on_request_score_update(data):
    """Handle request for score update"""
    try:
        session_id = data.get('session_id')
        if not session_id:
            emit('error', {'message': 'Missing session_id'})
            return
        
        # Get real-time score
        score = analytics_service.calculate_real_time_score(session_id)
        
        emit('score_update', {
            'session_id': session_id,
            'score': score
        }, room=session_id)
        
    except Exception as e:
        logger.error(f"Error getting score update: {e}")
        emit('error', {'message': str(e)})

@socketio.on('session_control')
def on_session_control(data):
    """Handle session control commands"""
    try:
        session_id = data.get('session_id')
        action = data.get('action')
        
        if not session_id or not action:
            emit('error', {'message': 'Missing session_id or action'})
            return
        
        if action == 'pause':
            # Pause session
            session_service.update_session(session_id, {'status': 'paused'})
            emit('session_paused', {'session_id': session_id}, room=session_id)
            
        elif action == 'resume':
            # Resume session
            session_service.update_session(session_id, {'status': 'active'})
            emit('session_resumed', {'session_id': session_id}, room=session_id)
            
        elif action == 'reset':
            # Reset session (clear history but keep session)
            session_service.update_session(session_id, {
                'call_events': [],
                'metrics': {
                    'total_duration': 0,
                    'questions_asked': 0,
                    'information_gathered': [],
                    'performance_score': 0
                }
            })
            emit('session_reset', {'session_id': session_id}, room=session_id)
        
    except Exception as e:
        logger.error(f"Error handling session control: {e}")
        emit('error', {'message': str(e)})

# Event bus handlers for real-time updates
def setup_event_handlers():
    """Setup event bus handlers for real-time updates"""
    
    def handle_analytics_update(event):
        """Handle analytics updates"""
        try:
            session_id = event.get('session_id')
            if session_id:
                socketio.emit('analytics_update', event['payload'], room=session_id)
        except Exception as e:
            logger.error(f"Error handling analytics update: {e}")
    
    def handle_emotional_state_change(event):
        """Handle emotional state changes"""
        try:
            session_id = event.get('session_id')
            if session_id:
                socketio.emit('emotional_state_changed', event['payload'], room=session_id)
        except Exception as e:
            logger.error(f"Error handling emotional state change: {e}")
    
    # Subscribe to relevant events
    event_bus.subscribe_to_events(['analytics.score_updated'], handle_analytics_update)
    event_bus.subscribe_to_events(['caller.emotion_changed'], handle_emotional_state_change)

# Initialize event handlers when module is imported
setup_event_handlers()
