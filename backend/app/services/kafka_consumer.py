import json
import logging
from kafka import KafkaConsumer
from typing import Dict, Any, Callable, List
from threading import Thread
from app.config import settings

logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self):
        self.consumers = {}
        self.running = False
        
    def create_consumer(self, topics: List[str], group_id: str) -> KafkaConsumer:
        """Create a Kafka consumer for specific topics"""
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                auto_offset_reset=settings.kafka_auto_offset_reset,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            logger.info(f"Created consumer for topics {topics} with group {group_id}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            return None
    
    def start_consumer(self, topics: List[str], group_id: str, message_handler: Callable):
        """Start consuming messages from topics"""
        def consume_messages():
            consumer = self.create_consumer(topics, group_id)
            if not consumer:
                logger.error(f"Failed to create consumer for group {group_id}")
                return
                
            self.consumers[group_id] = consumer
            logger.info(f"Starting consumer for group {group_id}")
            
            try:
                while self.running:
                    try:
                        message_batch = consumer.poll(timeout_ms=1000)
                        
                        for topic_partition, messages in message_batch.items():
                            for message in messages:
                                try:
                                    message_handler(message.value, message.topic)
                                except Exception as e:
                                    logger.error(f"Error processing message: {e}")
                                    
                    except Exception as e:
                        logger.error(f"Error in consumer loop: {e}")
                        
            except KeyboardInterrupt:
                logger.info("Consumer interrupted")
            finally:
                consumer.close()
                logger.info(f"Consumer {group_id} closed")
        
        self.running = True
        thread = Thread(target=consume_messages, daemon=True)
        thread.start()
        return thread
    
    def stop_all_consumers(self):
        """Stop all running consumers"""
        self.running = False
        for group_id, consumer in self.consumers.items():
            try:
                consumer.close()
                logger.info(f"Stopped consumer {group_id}")
            except Exception as e:
                logger.error(f"Error stopping consumer {group_id}: {e}")

kafka_consumer_service = KafkaConsumerService()