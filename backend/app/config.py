import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
    KAFKA_TOPIC_PREFIX = os.environ.get('KAFKA_TOPIC_PREFIX', 'ai_911')
    
    # Azure Speech Services
    AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION')
    
    # Model Configuration
    MODEL_PATH = os.environ.get('MODEL_PATH', './data/models')
    BASE_MODEL_NAME = os.environ.get('BASE_MODEL_NAME', 'meta-llama/Llama-2-7b-chat-hf')
    HUGGING_FACE_TOKEN = os.environ.get('HUGGING_FACE_TOKEN')
    
    # GPU Configuration
    USE_GPU = os.environ.get('USE_GPU', 'true').lower() == 'true'
    CUDA_VISIBLE_DEVICES = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
    
    # Performance Settings
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', '50'))
    STT_CHUNK_SIZE = int(os.environ.get('STT_CHUNK_SIZE', '1024'))
    AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', '16000'))
    
    # Security
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
