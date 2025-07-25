import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info("Kafka producer connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None
    
    def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Send message to Kafka topic"""
        if not self.producer:
            logger.warning("Kafka producer not available, skipping message")
            return False
        
        try:
            future = self.producer.send(topic, value=message, key=key)
            # Wait for message to be sent (optional, can be async)
            record_metadata = future.get(timeout=1)
            logger.debug(f"Message sent to {topic}: {record_metadata}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            return False
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()

# Global Kafka service instance
kafka_service = KafkaService()