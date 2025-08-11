from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import db

class CallLog(db.Model):
    __tablename__ = 'call_logs'
    
    call_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(UUID(as_uuid=True), nullable=False)
    trainee_id = db.Column(UUID(as_uuid=True), nullable=False)
    model_version = db.Column(db.String(20), nullable=False)
    audio_recording_id = db.Column(UUID(as_uuid=True))
    transcript = db.Column(db.Text)
    emotional_timeline = db.Column(JSONB)
    call_events = db.Column(JSONB)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    call_duration = db.Column(db.Integer)  # in seconds
    completed_successfully = db.Column(db.Boolean, default=False)
    performance_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'call_id': str(self.call_id),
            'scenario_id': str(self.scenario_id),
            'trainee_id': str(self.trainee_id),
            'model_version': self.model_version,
            'audio_recording_id': str(self.audio_recording_id) if self.audio_recording_id else None,
            'transcript': self.transcript,
            'emotional_timeline': self.emotional_timeline,
            'call_events': self.call_events,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'call_duration': self.call_duration,
            'completed_successfully': self.completed_successfully,
            'performance_score': self.performance_score
        }
