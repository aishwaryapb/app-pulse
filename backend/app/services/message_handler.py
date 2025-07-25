import json
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Type
from sqlalchemy.orm import Session
from app.services.memory_storage import memory_storage
from app.database.connection import get_sync_session
from app.models.database import APIMetric, SystemMetric, APIError, UIError

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.batch_size = 2
        self.batch_buffer = {}
        
        # Topic configuration with handlers and field mappings
        self.topic_config = {
            "api-metrics": {
                "memory_handler": memory_storage.add_api_metric,
                "db_model": APIMetric,
                "field_mapping": {
                    "timestamp": ("timestamp", self._parse_timestamp),
                    "data.method": "method",
                    "data.path": "path", 
                    "data.status_code": "status_code",
                    "data.response_time_ms": "response_time_ms",
                    "data.success": "success"
                },
                "store_in_db": True
            },
            "system-metrics": {
                "memory_handler": memory_storage.add_system_metric,
                "db_model": SystemMetric,
                "field_mapping": {
                    "timestamp": ("timestamp", self._parse_timestamp),
                    "data.cpu_percent": "cpu_percent",
                    "data.memory_percent": "memory_percent",
                    "data.disk_usage": "disk_usage",
                    "data.process_memory": "process_memory"
                },
                "store_in_db": True
            },
            "api-errors": {
                "memory_handler": memory_storage.add_api_error,
                "db_model": APIError,
                "field_mapping": {
                    "timestamp": ("timestamp", self._parse_timestamp),
                    "data.error_type": "error_type",
                    "data.error_message": "error_message",
                    "data.additional_data": ("additional_data", lambda x: json.dumps(x or {}))
                },
                "store_in_db": True
            },
            "ui-errors": {
                "memory_handler": memory_storage.add_ui_error,
                "db_model": UIError,
                "field_mapping": {
                    "timestamp": ("timestamp", self._parse_timestamp),
                    "data.error_type": "error_type",
                    "data.error_message": "error_message",
                    "data.user_id": "user_id",
                    "data.additional_data": ("additional_data", lambda x: json.dumps(x or {}))
                },
                "store_in_db": True
            }
        }
        
        # Initialize batch buffers
        for topic in self.topic_config:
            if self.topic_config[topic]["store_in_db"]:
                self.batch_buffer[topic] = []
    
    def handle_kafka_message(self, message: Dict[str, Any], topic: str):
        """Route Kafka messages to appropriate handlers"""
        try:
            logger.debug(f"Processing message from topic {topic}")
            
            config = self.topic_config.get(topic)
            if not config:
                logger.warning(f"Unknown topic: {topic}")
                return
            
            # Always add to memory storage for real-time updates
            config["memory_handler"](message)
            
            # Add to database batch if configured
            if config["store_in_db"]:
                self._add_to_batch(topic, message)
                
        except Exception as e:
            logger.error(f"Error handling message from {topic}: {e}")
    
    def _add_to_batch(self, topic: str, message: Dict[str, Any]):
        """Add message to batch and flush if batch is full"""
        self.batch_buffer[topic].append(message)
        
        if len(self.batch_buffer[topic]) >= self.batch_size:
            self._flush_batch_to_db(topic)
    
    def _flush_batch_to_db(self, topic: str):
        """Flush batch to database"""
        try:
            config = self.topic_config[topic]
            if not config["store_in_db"]:
                return
            logger.info(f"Flushing batch - ${topic}")
            db = next(get_sync_session())
            
            for message in self.batch_buffer[topic]:
                # Generic mapping using field_mapping configuration
                db_object = self._map_message_to_model(message, config)
                if db_object:
                    logger.info("Adding to db")
                    db.add(db_object)
            
            db.commit()
            logger.info(f"Flushed {len(self.batch_buffer[topic])} messages from {topic} to database")
            
        except Exception as e:
            logger.error(f"Error flushing {topic} to database: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
            self.batch_buffer[topic].clear()
    
    def _map_message_to_model(self, message: Dict[str, Any], config: Dict[str, Any]):
        """Generic mapping from message to database model"""
        model_class = config["db_model"]
        field_mapping = config["field_mapping"]
        
        if not model_class or not field_mapping:
            return None
        
        model_kwargs = {}
        
        for source_path, target_config in field_mapping.items():
            # Handle tuple format (field_name, transformer_function)
            if isinstance(target_config, tuple):
                target_field, transformer = target_config
            else:
                target_field = target_config
                transformer = None
            
            # Extract value from message using dot notation
            value = self._get_nested_value(message, source_path)
            
            # Apply transformer if provided
            if transformer and value is not None:
                try:
                    value = transformer(value)
                except Exception as e:
                    logger.warning(f"Error transforming field {source_path}: {e}")
                    continue
            
            model_kwargs[target_field] = value
        
        return model_class(**model_kwargs)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str):
        """Get value from nested dictionary using dot notation (e.g., 'data.method')"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return datetime.utcnow()
        
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return datetime.utcnow()
    
    def flush_all_batches(self):
        """Flush all pending batches to database (useful for shutdown)"""
        logger.info("Flushing all the batches to db")
        for topic in self.batch_buffer:
            if self.batch_buffer[topic]:
                self._flush_batch_to_db(topic)

# Global message handler instance
message_handler = MessageHandler()