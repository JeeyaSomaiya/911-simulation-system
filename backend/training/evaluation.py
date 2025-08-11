import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import numpy as np
from sklearn.metrics import accuracy_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self, base_model_name="meta-llama/Llama-2-7b-chat-hf"):
        self.base_model_name = base_model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.base_model = None
        self.fine_tuned_model = None
        
    def load_models(self, fine_tuned_model_path, hf_token=None):
        """Load base and fine-tuned models"""
        logger.info("Loading models for evaluation...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            use_auth_token=hf_token
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model
        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            use_auth_token=hf_token
        )
        
        # Load fine-tuned model
        self.fine_tuned_model = PeftModel.from_pretrained(
            self.base_model,
            fine_tuned_model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )
        
        logger.info("Models loaded successfully")
    
    def generate_response(self, model, prompt, max_length=150):
        """Generate response using the model"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )
        
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        ).strip()
        
        return response
    
    def evaluate_scenario_compliance(self, conversations, model):
        """Evaluate how well the model stays within scenario bounds"""
        compliance_scores = []
        
        for conv in conversations:
            scenario_type = conv['scenario_type']
            context = conv['context']
            
            # Create test prompt
            prompt = f"<|scenario|>{scenario_type}\n<|context|>{json.dumps(context)}\n<|conversation|>\nDispatcher: 911, what's your emergency?\nCaller ["
            
            # Generate response
            response = self.generate_response(model, prompt)
            
            # Evaluate compliance (simplified scoring)
            compliance_score = self.score_scenario_compliance(response, scenario_type, context)
            compliance_scores.append(compliance_score)
        
        return np.mean(compliance_scores)
    
    def score_scenario_compliance(self, response, scenario_type, context):
        """Score how well a response complies with the scenario"""
        score = 0.0
        
        # Check for scenario-specific keywords
        scenario_keywords = {
            'house_fire': ['fire', 'smoke', 'house', 'burning'],
            'medical_emergency': ['chest', 'pain', 'heart', 'medical', 'sick'],
            'robbery': ['robbery', 'gun', 'weapon', 'steal', 'robber']
        }
        
        keywords = scenario_keywords.get(scenario_type, [])
        response_lower = response.lower()
        
        # Score based on keyword presence
        for keyword in keywords:
            if keyword in response_lower:
                score += 0.25
        
        # Check for context information
        if context and context.get('emergency_details'):
            details = context['emergency_details']
            for key, value in details.items():
                if isinstance(value, str) and any(word in response_lower for word in value.lower().split()):
                    score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def evaluate_emotional_consistency(self, conversations, model):
        """Evaluate emotional consistency in responses"""
        consistency_scores = []
        
        for conv in conversations:
            emotional_progression = conv.get('emotional_progression', [])
            
            if not emotional_progression:
                continue
            
            # Test different emotional states
            for emotion_data in emotional_progression[:3]:  # Test first 3 states
                state = emotion_data['state']
                intensity = emotion_data['intensity']
                
                prompt = f"<|scenario|>{conv['scenario_type']}\n<|initial_emotion|>{state}:{intensity}\n<|conversation|>\nDispatcher: Can you tell me what's happening?\nCaller [{state}:{intensity}]: "
                
                response = self.generate_response(model, prompt)
                
                # Score emotional consistency
                consistency_score = self.score_emotional_consistency(response, state, intensity)
                consistency_scores.append(consistency_score)
        
        return np.mean(consistency_scores) if consistency_scores else 0.0
    
    def score_emotional_consistency(self, response, expected_state, intensity):
        """Score emotional consistency of a response"""
        response_lower = response.lower()
        
        # Emotional indicators
        emotional_indicators = {
            'CALM': ['okay', 'alright', 'fine', 'thank you'],
            'WORRIED': ['worried', 'concerned', 'nervous', 'anxious'],
            'PANICKED': ['help', 'please', 'urgent', 'hurry'],
            'HYSTERICAL': ['oh god', 'please help', 'dying', 'can\'t'],
            'RELIEVED': ['thank god', 'better', 'okay now', 'relieved']
        }
        
        indicators = emotional_indicators.get(expected_state, [])
        
        # Base score from indicators
        score = 0.5  # Base score
        
        for indicator in indicators:
            if indicator in response_lower:
                score += 0.2
        
        # Adjust for intensity
        if intensity > 7:  # High intensity
            if any(char in response for char in ['!', '?']):
                score += 0.1
            if response.isupper():  # All caps for extreme emotion
                score += 0.1
        elif intensity < 4:  # Low intensity
            if '.' in response and '!' not in response:
                score += 0.1
        
        return min(score, 1.0)
    
    def calculate_perplexity(self, conversations, model):
        """Calculate perplexity of the model on test data"""
        total_loss = 0
        total_tokens = 0
        
        model.eval()
        
        for conv in conversations[:10]:  # Test on subset for speed
            # Format conversation
            text = self.format_conversation_for_evaluation(conv)
            
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            )
            
            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Calculate loss
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs['input_ids'])
                loss = outputs.loss
                
                total_loss += loss.item() * inputs['input_ids'].shape[1]
                total_tokens += inputs['input_ids'].shape[1]
        
        perplexity = torch.exp(torch.tensor(total_loss / total_tokens))
        return perplexity.item()
    
    def format_conversation_for_evaluation(self, conversation):
        """Format conversation for evaluation"""
        scenario_type = conversation['scenario_type']
        turns = conversation['conversation']
        
        formatted_text = f"<|scenario|>{scenario_type}\n<|conversation|>\n"
        
        for turn in turns:
            role = turn['role']
            content = turn['content']
            
            if role == 'dispatcher':
                formatted_text += f"Dispatcher: {content}\n"
            elif role == 'caller':
                emotion = turn.get('emotional_state', 'WORRIED')
                intensity = turn.get('intensity', 5)
                formatted_text += f"Caller [{emotion}:{intensity}]: {content}\n"
        
        return formatted_text
    
    def comprehensive_evaluation(self, test_conversations, fine_tuned_model_path):
        """Run comprehensive evaluation"""
        logger.info("Starting comprehensive evaluation...")
        
        results = {}
        
        # Scenario compliance
        logger.info("Evaluating scenario compliance...")
        base_compliance = self.evaluate_scenario_compliance(test_conversations, self.base_model)
        fine_tuned_compliance = self.evaluate_scenario_compliance(test_conversations, self.fine_tuned_model)
        
        results['scenario_compliance'] = {
            'base_model': base_compliance,
            'fine_tuned_model': fine_tuned_compliance,
            'improvement': fine_tuned_compliance - base_compliance
        }
        
        # Emotional consistency
        logger.info("Evaluating emotional consistency...")
        base_emotional = self.evaluate_emotional_consistency(test_conversations, self.base_model)
        fine_tuned_emotional = self.evaluate_emotional_consistency(test_conversations, self.fine_tuned_model)
        
        results['emotional_consistency'] = {
            'base_model': base_emotional,
            'fine_tuned_model': fine_tuned_emotional,
            'improvement': fine_tuned_emotional - base_emotional
        }
        
        # Perplexity
        logger.info("Calculating perplexity...")
        base_perplexity = self.calculate_perplexity(test_conversations, self.base_model)
        fine_tuned_perplexity = self.calculate_perplexity(test_conversations, self.fine_tuned_model)
        
        results['perplexity'] = {### Step 14: Training Data and Model Implementation
```bash
cat > training/data_preparation.py << 'EOF'
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import random

def generate@api_bp.route('/analytics/<session_id>/score', methods=['GET'])
def get_real_time_score(session_id):
    """Get real-time performance score"""
    try:
        score = analytics_service.calculate_real_time_score(session_id)
        return jsonify(score)
        
    except Exception as e:
        logger.error(f"Error getting real-time score: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analytics/aggregate', methods=['GET'])
def get_aggregate_analytics():
    """Get aggregate analytics"""
    try:
        timeframe = request.args.get('timeframe_hours', 24, type=int)
        analytics = analytics_service.get_aggregate_analytics(timeframe)
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting aggregate analytics: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/datasets', methods=['POST'])
def create_training_dataset():
    """Create a new training dataset"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        conversations = data.get('conversations', [])
        
        if not name or not conversations:
            return jsonify({'error': 'Missing required fields'}), 400
        
        dataset_id = training_data_service.create_dataset(
            name=name,
            description=description,
            conversations=conversations
        )
        
        # Save to database
        dataset = TrainingDataset(
            dataset_id=dataset_id,
            dataset_name=name,
            version='1.0.0',
            conversation_count=len(conversations),
            quality_score=0.8,  # Would be calculated
            metadata={'description': description},
            s3_path=f"training_datasets/{dataset_id}.json"
        )
        
        db.session.add(dataset)
        db.session.commit()
        
        return jsonify({
            'dataset_id': dataset_id,
            'status': 'created',
            'conversation_count': len(conversations)
        })
        
    except Exception as e:
        logger.error(f"Error creating training dataset: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/datasets', methods=['GET'])
def list_training_datasets():
    """List all training datasets"""
    try:
        datasets = training_data_service.list_datasets()
        return jsonify({'datasets': datasets})
        
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/datasets/<dataset_id>/validate', methods=['POST'])
def validate_dataset(dataset_id):
    """Validate a training dataset"""
    try:
        validation_result = training_data_service.validate_dataset(dataset_id)
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"Error validating dataset: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/start', methods=['POST'])
def start_model_training():
    """Start model training"""
    try:
        data = request.get_json()
        
        dataset_id = data.get('dataset_id')
        training_config = data.get('config', {})
        
        if not dataset_id:
            return jsonify({'error': 'Missing dataset_id'}), 400
        
        training_id = ml_training_service.start_training(
            dataset_id=dataset_id,
            training_config=training_config
        )
        
        return jsonify({
            'training_id': training_id,
            'status': 'started',
            'dataset_id': dataset_id
        })
        
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/<training_id>/status', methods=['GET'])
def get_training_status(training_id):
    """Get training job status"""
    try:
        status = ml_training_service.get_training_status(training_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/training/jobs', methods=['GET'])
def list_training_jobs():
    """List all training jobs"""
    try:
        jobs = ml_training_service.list_training_jobs()
        return jsonify({'training_jobs': jobs})
        
    except Exception as e:
        logger.error(f"Error listing training jobs: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/models', methods=['GET'])
def list_models():
    """List all trained models"""
    try:
        models = ModelRegistry.query.all()
        return jsonify({
            'models': [model.to_dict() for model in models]
        })
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/models/<model_id>/deploy', methods=['POST'])
def deploy_model(model_id):
    """Deploy a trained model"""
    try:
        model = ModelRegistry.query.filter_by(model_id=model_id).first()
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        # Update deployment status
        model.deployment_status = 'deployed'
        model.deployed_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'model_id': model_id,
            'status': 'deployed',
            'deployed_at': model.deployed_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        return jsonify({'error': str(e)}), 500
