import json
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, List
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import asyncio
import threading
import logging

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self, bootstrap_servers: List[str], topic_prefix: str = 'ai_911'):
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.producer = None
        self.consumers = {}
        self.event_handlers = {}
        self.running = False
        
    def initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                acks='all'
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def publish_event(self, event_type: str, payload: Dict[Any, Any], 
                     session_id: str = None, source_service: str = None,
                     model_version: str = None):
        """Publish an event to Kafka topic"""
        if not self.producer:
            self.initialize_producer()
        
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "source_service": source_service or "unknown",
            "payload": payload,
            "correlation_id": str(uuid.uuid4()),
            "version": "1.0.0",
            "model_version": model_version
        }
        
        topic = f"{self.topic_prefix}.{event_type.replace('.', '_')}"
        
        try:
            future = self.producer.send(
                topic,
                value=event,
                key=session_id
            )
            future.get(timeout=10)  # Wait for acknowledgment
            logger.debug(f"Event published successfully: {event_type}")
        except KafkaError as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise
    
    def subscribe_to_events(self, event_types: List[str], handler: Callable):
        """Subscribe to specific event types"""
        for event_type in event_types:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
            
            # Start consumer for this event type if not already running
            topic = f"{self.topic_prefix}.{event_type.replace('.', '_')}"
            if topic not in self.consumers:
                self._start_consumer_for_topic(topic, event_type)
    
    def _start_consumer_for_topic(self, topic: str, event_type: str):
        """Start a consumer for a specific topic"""
        def consume_messages():
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest',
                    group_id=f"ai_911_consumer_{event_type}"
                )
                
                self.consumers[topic] = consumer
                logger.info(f"Started consumer for topic: {topic}")
                
                for message in consumer:
                    if not self.running:
                        break
                        
                    event = message.value
                    event_type = event.get('event_type')
                    
                    # Call all handlers for this event type
                    if event_type in self.event_handlers:
                        for handler in self.event_handlers[event_type]:
                            try:
                                handler(event)
                            except Exception as e:
                                logger.error(f"Error in event handler for {event_type}: {e}")
                
            except Exception as e:
                logger.error(f"Consumer error for topic {topic}: {e}")
                
        # Start consumer in separate thread
        consumer_thread = threading.Thread(target=consume_messages)
        consumer_thread.daemon = True
        consumer_thread.start()
    
    def start(self):
        """Start the event bus"""
        self.running = True
        self.initialize_producer()
        logger.info("Event bus started")
    
    def stop(self):
        """Stop the event bus"""
        self.running = False
        if self.producer:
            self.producer.close()
        for consumer in self.consumers.values():
            consumer.close()
        logger.info("Event bus stopped")

# Global event bus instance
event_bus = EventBus([], "ai_911")  # Will be initialized with proper config
