from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import db

class TrainingDataset(db.Model):
    __tablename__ = 'training_datasets'
    
    dataset_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    conversation_count = db.Column(db.Integer, nullable=False)
    quality_score = db.Column(db.Numeric(3, 2))
    metadata = db.Column(JSONB)
    s3_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'dataset_id': str(self.dataset_id),
            'dataset_name': self.dataset_name,
            'version': self.version,
            'conversation_count': self.conversation_count,
            'quality_score': float(self.quality_score) if self.quality_score else None,
            'metadata': self.metadata,
            's3_path': self.s3_path,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
