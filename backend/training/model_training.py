import os
import json
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, TrainingArguments, 
    Trainer, DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AI911ModelTrainer:
    def __init__(self, base_model_name="meta-llama/Llama-2-7b-chat-hf"):
        self.base_model_name = base_model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # LoRA configuration for efficient fine-tuning
        self.lora_config = LoraConfig(
            r=64,  # Low-rank adaptation rank
            lora_alpha=16,  # LoRA scaling parameter
            target_modules=[
                "q_proj", "v_proj", "k_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
        self.tokenizer = None
        self.model = None
        
    def initialize(self, hf_token=None):
        """Initialize tokenizer and model"""
        logger.info("Initializing tokenizer and model...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            use_auth_token=hf_token
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            use_auth_token=hf_token
        )
        
        logger.info(f"Model loaded on device: {self.device}")
        
    def format_conversation_for_training(self, conversation):
        """Format conversation data for training"""
        
        scenario_type = conversation['scenario_type']
        context = conversation['context']
        turns = conversation['conversation']
        emotional_progression = conversation.get('emotional_progression', [])
        
        # Build the training text
        formatted_text = f"<|scenario|>{scenario_type}\n"
        
        # Add context information
        if context:
            formatted_text += f"<|context|>{json.dumps(context)}\n"
        
        # Add emotional progression
        if emotional_progression:
            initial_emotion = emotional_progression[0]
            formatted_text += f"<|initial_emotion|>{initial_emotion['state']}:{initial_emotion['intensity']}\n"
        
        # Add conversation
        formatted_text += "<|conversation|>\n"
        
        for turn in turns:
            role = turn['role']
            content = turn['content']
            
            if role == 'dispatcher':
                formatted_text += f"Dispatcher: {content}\n"
            elif role == 'caller':
                emotion = turn.get('emotional_state', 'WORRIED')
                intensity = turn.get('intensity', 5)
                formatted_text += f"Caller [{emotion}:{intensity}]: {content}\n"
        
        formatted_text += "<|end|>"
        
        return formatted_text
    
    def prepare_dataset(self, conversations):
        """Prepare dataset for training"""
        logger.info(f"Preparing dataset with {len(conversations)} conversations...")
        
        # Format conversations
        formatted_texts = []
        for conv in conversations:
            formatted_text = self.format_conversation_for_training(conv)
            formatted_texts.append(formatted_text)
        
        # Create dataset
        dataset = Dataset.from_dict({"text": formatted_texts})
        
        # Tokenize dataset
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=2048,
                return_tensors="pt"
            )
            tokenized["labels"] = tokenized["input_ids"].clone()
            return tokenized
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset
    
    def train_model(self, dataset, output_dir="./models/ai_911_model", num_epochs=3):
        """Train the model using LoRA"""
        logger.info("Starting model training...")
        
        # Apply LoRA to the model
        peft_model = get_peft_model(self.model, self.lora_config)
        peft_model.print_trainable_parameters()
        
        # Split dataset
        train_size = int(0.9 * len(dataset))
        train_dataset = dataset.select(range(train_size))
        eval_dataset = dataset.select(range(train_size, len(dataset)))
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=8,
            warmup_steps=100,
            learning_rate=2e-4,
            fp16=self.device == "cuda",
            logging_steps=10,
            save_steps=500,
            eval_steps=500,
            evaluation_strategy="steps",
            save_strategy="steps",
            dataloader_drop_last=True,
            remove_unused_columns=False,
            report_to=None  # Disable wandb/tensorboard for simplicity
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=peft_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )
        
        # Start training
        logger.info("Training started...")
        trainer.train()
        
        # Save the model
        trainer.save_model(output_dir)
        logger.info(f"Model saved to {output_dir}")
        
        return trainer
    
    def load_training_data(self, data_path):
        """Load training data from file"""
        with open(data_path, 'r') as f:
            conversations = json.load(f)
        
        logger.info(f"Loaded {len(conversations)} conversations from {data_path}")
        return conversations

def main():
    """Main training function"""
    
    # Initialize trainer
    trainer = AI911ModelTrainer()
    
    # Get Hugging Face token from environment
    hf_token = os.getenv('HUGGING_FACE_TOKEN')
    if not hf_token:
        logger.error("HUGGING_FACE_TOKEN not found in environment variables")
        return
    
    # Initialize model
    trainer.initialize(hf_token)
    
    # Load training data
    training_data_path = "./data/training_datasets/sample_training_data.json"
    if not os.path.exists(training_data_path):
        logger.error(f"Training data not found at {training_data_path}")
        logger.info("Please run data_preparation.py first to generate training data")
        return
    
    conversations = trainer.load_training_data(training_data_path)
    
    # Prepare dataset
    dataset = trainer.prepare_dataset(conversations)
    
    # Create output directory
    output_dir = "./data/models/ai_911_fine_tuned"
    os.makedirs(output_dir, exist_ok=True)
    
    # Train model
    trainer.train_model(dataset, output_dir, num_epochs=3)
    
    logger.info("Training completed successfully!")

if __name__ == "__main__":
    main()
