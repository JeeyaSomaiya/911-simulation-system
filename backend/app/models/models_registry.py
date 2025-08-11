from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import db

class ModelRegistry(db.Model):
    __tablename__ = 'models'
    
    model_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    base_model = db.Column(db.String(100), nullable=False)
    training_dataset_id = db.Column(UUID(as_uuid=True), db.ForeignKey('training_datasets.dataset_id'))
    performance_metrics = db.Column(JSONB)
    deployment_status = db.Column(db.String(20), default='training')  # training, testing, deployed, archived
    model_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'model_id': str(self.model_id),
            'model_name': self.model_name,
            'version': self.version,
            'base_model': self.base_model,
            'training_dataset_id': str(self.training_dataset_id) if self.training_dataset_id else None,
            'performance_metrics': self.performance_metrics,
            'deployment_status': self.deployment_status,
            'model_path': self.model_path,
            'created_at': self.created_at.isoformat(),
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None
        }
