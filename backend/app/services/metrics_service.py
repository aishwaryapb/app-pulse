import time
import psutil
from datetime import datetime
from typing import Dict, Any
from app.services.kafka_service import kafka_service

class MetricsService:
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get system-level metrics (CPU, memory, etc.)"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "apppulse-backend",
            "type": "system_metrics",
            "data": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "process_memory": psutil.Process().memory_info().rss / 1024 / 1024  # MB
            }
        }
    
    @staticmethod
    def create_api_metrics(method: str, path: str, status_code: int, response_time: float) -> Dict[str, Any]:
        """Create API metrics payload"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "apppulse-backend",
            "type": "api_metrics",
            "data": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time_ms": round(response_time * 1000, 2),
                "success": status_code < 400
            }
        }
    
    @staticmethod
    def send_api_metrics(method: str, path: str, status_code: int, response_time: float):
        """Send API metrics to Kafka"""
        metrics = MetricsService.create_api_metrics(method, path, status_code, response_time)
        kafka_service.send_message("api-metrics" ,metrics)
    
    @staticmethod
    def send_api_error(method: str, path: str, status_code: int, response_time: float, exception: Exception = None):
        """Send API error to Kafka"""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "apppulse-backend",
            "type": "api_errors",
            "data": {
                "error_type": type(exception).__name__ if exception else f"HTTP_{status_code}",
                "error_message": str(exception) if exception else f"HTTP {status_code} Error",
                "additional_data": {
                    "method": method,
                    "path":path,
                    "status_code": status_code,
                    "response_time_ms": round(response_time * 1000, 2),
                }
            }
        }
        kafka_service.send_message("api-errors", error_data)
    
    @staticmethod
    def send_system_metrics():
        """Send system metrics to Kafka"""
        metrics = MetricsService.get_system_metrics()
        kafka_service.send_message("system-metrics", metrics)

metrics_service = MetricsService()