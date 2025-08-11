import logging
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import re
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class TrainingDataService:
    def __init__(self, data_path: str = "./data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_path / "training_datasets").mkdir(exist_ok=True)
        (self.data_path / "raw_conversations").mkdir(exist_ok=True)
        (self.data_path / "processed").mkdir(exist_ok=True)
        (self.data_path / "validation").mkdir(exist_ok=True)
        
        self.datasets = {}
        
    def initialize(self):
        """Initialize training data service"""
        try:
            # Load existing datasets metadata
            self._load_datasets_metadata()
            logger.info("Training data service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize training data service: {e}")
            raise
    
    def create_dataset(self, name: str, description: str, 
                      conversations: List[Dict[str, Any]]) -> str:
        """Create a new training dataset"""
        try:
            dataset_id = str(uuid.uuid4())
            
            # Validate and clean conversations
            cleaned_conversations = self._validate_and_clean_conversations(conversations)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(cleaned_conversations)
            
            # Create dataset metadata
            dataset_metadata = {
                'dataset_id': dataset_id,
                'name': name,
                'description': description,
                'version': '1.0.0',
                'created_at': datetime.utcnow().isoformat(),
                'conversation_count': len(cleaned_conversations),
                'quality_score': quality_metrics['overall_score'],
                'quality_metrics': quality_metrics,
                'file_path': f"training_datasets/{dataset_id}.json",
                'metadata': {
                    'scenario_distribution': self._analyze_scenario_distribution(cleaned_conversations),
                    'emotional_distribution': self._analyze_emotional_distribution(cleaned_conversations),
                    'conversation_lengths': self._analyze_conversation_lengths(cleaned_conversations)
                }
            }
            
            # Save conversations to file
            dataset_file = self.data_path / f"training_datasets/{dataset_id}.json"
            with open(dataset_file, 'w') as f:
                json.dump(cleaned_conversations, f, indent=2)
            
            # Save metadata
            metadata_file = self.data_path / f"training_datasets/{dataset_id}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(dataset_metadata, f, indent=2)
            
            # Update in-memory registry
            self.datasets[dataset_id] = dataset_metadata
            
            logger.info(f"Created dataset {dataset_id} with {len(cleaned_conversations)} conversations")
            
            return dataset_id
            
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            raise
    
    def _validate_and_clean_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean conversation data"""
        cleaned = []
        
        for conv in conversations:
            try:
                # Validate required fields
                if not all(key in conv for key in ['conversation_id', 'scenario_type', 'conversation']):
                    logger.warning(f"Skipping conversation with missing required fields")
                    continue
                
                # Clean conversation turns
                cleaned_turns = []
                for turn in conv['conversation']:
                    if 'role' in turn and 'content' in turn:
                        # Clean content
                        cleaned_content = self._clean_text(turn['content'])
                        if cleaned_content:  # Only include non-empty content
                            cleaned_turn = {
                                'role': turn['role'],
                                'content': cleaned_content,
                                'timestamp': turn.get('timestamp', 0)
                            }
                            
                            # Add emotional state if available
                            if turn['role'] == 'caller':
                                cleaned_turn['emotional_state'] = turn.get('emotional_state', 'WORRIED')
                                cleaned_turn['intensity'] = turn.get('intensity', 5)
                            
                            cleaned_turns.append(cleaned_turn)
                
                # Only include conversations with sufficient turns
                if len(cleaned_turns) >= 4:  # At least 2 exchanges
                    cleaned_conv = {
                        'conversation_id': conv['conversation_id'],
                        'scenario_type': conv['scenario_type'],
                        'conversation': cleaned_turns,
                        'emotional_progression': conv.get('emotional_progression', []),
                        'context': conv.get('context', {})
                    }
                    cleaned.append(cleaned_conv)
                
            except Exception as e:
                logger.warning(f"Error processing conversation {conv.get('conversation_id', 'unknown')}: {e}")
                continue
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean and anonymize text"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove or replace PII
        text = self._remove_pii(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove very short or very long texts
        if len(text) < 3 or len(text) > 500:
            return ""
        
        return text
    
    def _remove_pii(self, text: str) -> str:
        """Remove personally identifiable information"""
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Social Security Numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Credit card numbers (simplified)
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Specific addresses (simplified pattern)
        text = re.sub(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b', '[ADDRESS]', text, flags=re.IGNORECASE)
        
        return text
    
    def _calculate_quality_metrics(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the dataset"""
        if not conversations:
            return {'overall_score': 0.0}
        
        metrics = {
            'total_conversations': len(conversations),
            'avg_conversation_length': 0,
            'emotional_state_coverage': 0,
            'scenario_diversity': 0,
            'data_completeness': 0,
            'overall_score': 0
        }
        
        # Calculate average conversation length
        lengths = [len(conv['conversation']) for conv in conversations]
        metrics['avg_conversation_length'] = sum(lengths) / len(lengths)
        
        # Emotional state coverage
        all_emotions = set()
        for conv in conversations:
            for turn in conv['conversation']:
                if turn['role'] == 'caller' and 'emotional_state' in turn:
                    all_emotions.add(turn['emotional_state'])
        
        expected_emotions = {'CALM', 'WORRIED', 'PANICKED', 'HYSTERICAL', 'RELIEVED'}
        metrics['emotional_state_coverage'] = len(all_emotions & expected_emotions) / len(expected_emotions)
        
        # Scenario diversity
        scenarios = set(conv['scenario_type'] for conv in conversations)
        expected_scenarios = {'house_fire', 'medical_emergency', 'robbery'}
        metrics['scenario_diversity'] = len(scenarios & expected_scenarios) / len(expected_scenarios)
        
        # Data completeness
        complete_conversations = 0
        for conv in conversations:
            has_emotional_progression = bool(conv.get('emotional_progression'))
            has_context = bool(conv.get('context'))
            has_sufficient_turns = len(conv['conversation']) >= 6
            
            if has_emotional_progression and has_context and has_sufficient_turns:
                complete_conversations += 1
        
        metrics['data_completeness'] = complete_conversations / len(conversations)
        
        # Overall score (weighted average)
        weights = {
            'emotional_state_coverage': 0.3,
            'scenario_diversity': 0.3,
            'data_completeness': 0.4
        }
        
        metrics['overall_score'] = sum(
            metrics[key] * weight for key, weight in weights.items()
        )
        
        return metrics
    
    def _analyze_scenario_distribution(self, conversations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of scenario types"""
        distribution = {}
        for conv in conversations:
            scenario = conv['scenario_type']
            distribution[scenario] = distribution.get(scenario, 0) + 1
        return distribution
    
    def _analyze_emotional_distribution(self, conversations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of emotional states"""
        distribution = {}
        for conv in conversations:
            for turn in conv['conversation']:
                if turn['role'] == 'caller' and 'emotional_state' in turn:
                    emotion = turn['emotional_state']
                    distribution[emotion] = distribution.get(emotion, 0) + 1
        return distribution
    
    def _analyze_conversation_lengths(self, conversations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze conversation length statistics"""
        lengths = [len(conv['conversation']) for conv in conversations]
        
        return {
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
            'mean': sum(lengths) / len(lengths) if lengths else 0,
            'median': sorted(lengths)[len(lengths)//2] if lengths else 0
        }
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset by ID"""
        try:
            if dataset_id in self.datasets:
                return self.datasets[dataset_id]
            
            # Try to load from file
            metadata_file = self.data_path / f"training_datasets/{dataset_id}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.datasets[dataset_id] = metadata
                    return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting dataset {dataset_id}: {e}")
            return None
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets"""
        return list(self.datasets.values())
    
    def load_dataset_conversations(self, dataset_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load conversations from a dataset"""
        try:
            dataset_file = self.data_path / f"training_datasets/{dataset_id}.json"
            if dataset_file.exists():
                with open(dataset_file, 'r') as f:
                    return json.load(f)
            
            logger.warning(f"Dataset file not found: {dataset_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading dataset conversations {dataset_id}: {e}")
            return None
    
    def validate_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Validate a dataset"""
        try:
            conversations = self.load_dataset_conversations(dataset_id)
            if not conversations:
                return {'valid': False, 'errors': ['Dataset not found']}
            
            errors = []
            warnings = []
            
            # Check for required fields
            for i, conv in enumerate(conversations):
                if 'conversation_id' not in conv:
                    errors.append(f"Conversation {i}: Missing conversation_id")
                
                if 'scenario_type' not in conv:
                    errors.append(f"Conversation {i}: Missing scenario_type")
                
                if 'conversation' not in conv or not conv['conversation']:
                    errors.append(f"Conversation {i}: Missing or empty conversation")
                
                # Check conversation turns
                for j, turn in enumerate(conv.get('conversation', [])):
                    if 'role' not in turn:
                        errors.append(f"Conversation {i}, turn {j}: Missing role")
                    if 'content' not in turn:
                        errors.append(f"Conversation {i}, turn {j}: Missing content")
            
            # Check data quality
            total_conversations = len(conversations)
            if total_conversations < 10:
                warnings.append("Dataset has fewer than 10 conversations")
            
            scenario_types = set(conv['scenario_type'] for conv in conversations)
            if len(scenario_types) < 2:
                warnings.append("Dataset lacks scenario diversity")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'total_conversations': total_conversations,
                'scenario_types': list(scenario_types)
            }
            
        except Exception as e:
            logger.error(f"Error validating dataset {dataset_id}: {e}")
            return {'valid': False, 'errors': [str(e)]}
    
    def _load_datasets_metadata(self):
        """Load metadata for all existing datasets"""
        try:
            datasets_dir = self.data_path / "training_datasets"
            for metadata_file in datasets_dir.glob("*_metadata.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        dataset_id = metadata['dataset_id']
                        self.datasets[dataset_id] = metadata
                except Exception as e:
                    logger.warning(f"Error loading metadata from {metadata_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading datasets metadata: {e}")

# Global service instance
training_data_service = TrainingDataService()
