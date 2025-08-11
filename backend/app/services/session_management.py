import logging
import redis
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManagementService:
    def __init__(self):
        self.redis_client = None
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
        
    def initialize(self, redis_url: str):
        """Initialize session management service"""
        try:
            self.redis_client = redis.from_url(redis_url)
            logger.info("Session management service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session management: {e}")
            raise
    
    def create_session(self, trainee_id: str, scenario_type: str, 
                      model_version: str = "v1.0") -> Dict[str, Any]:
        """Create a new training session"""
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                'session_id': session_id,
                'trainee_id': trainee_id,
                'scenario_type': scenario_type,
                'model_version': model_version,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'call_events': [],
                'metrics': {
                    'total_duration': 0,
                    'questions_asked': 0,
                    'information_gathered': [],
                    'performance_score': 0
                }
            }
            
            # Store in Redis
            self.redis_client.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session_data)
            )
            
            # Add to active sessions
            self.active_sessions[session_id] = session_data
            
            logger.info(f"Created session {session_id} for trainee {trainee_id}")
            
            return {
                'session_id': session_id,
                'status': 'created',
                'scenario_type': scenario_type,
                'created_at': session_data['created_at']
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            # Check active sessions first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Check Redis
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                session = json.loads(session_data)
                self.active_sessions[session_id] = session
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Update session data
            session.update(updates)
            session['last_activity'] = datetime.utcnow().isoformat()
            
            # Save to Redis
            self.redis_client.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session)
            )
            
            # Update active sessions
            self.active_sessions[session_id] = session
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def add_call_event(self, session_id: str, event_type: str, 
                      event_data: Dict[str, Any]) -> bool:
        """Add an event to the session timeline"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'data': event_data
            }
            
            session['call_events'].append(event)
            
            # Update session
            return self.update_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Error adding event to session {session_id}: {e}")
            return False
    
    def end_session(self, session_id: str, completion_status: str = 'completed') -> Dict[str, Any]:
        """End a training session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'error': 'Session not found'}
            
            # Calculate final metrics
            start_time = datetime.fromisoformat(session['created_at'])
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            # Update session with final data
            session.update({
                'status': completion_status,
                'ended_at': end_time.isoformat(),
                'total_duration': total_duration
            })
            
            # Save final state
            self.update_session(session_id, session)
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Session {session_id} ended with status: {completion_status}")
            
            return {
                'session_id': session_id,
                'status': completion_status,
                'total_duration': total_duration,
                'ended_at': session['ended_at']
            }
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")
            return {'error': str(e)}
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        try:
            active = []
            for session_id, session_data in self.active_sessions.items():
                if session_data.get('status') == 'active':
                    active.append({
                        'session_id': session_id,
                        'trainee_id': session_data.get('trainee_id'),
                        'scenario_type': session_data.get('scenario_type'),
                        'created_at': session_data.get('created_at'),
                        'last_activity': session_data.get('last_activity')
                    })
            
            return active
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_data in list(self.active_sessions.items()):
                last_activity = datetime.fromisoformat(session_data['last_activity'])
                if (current_time - last_activity).total_seconds() > self.session_timeout:
                    expired_sessions.append(session_id)
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                self.end_session(session_id, 'expired')
                logger.info(f"Cleaned up expired session: {session_id}")
            
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

# Global service instance
session_service = SessionManagementService()
