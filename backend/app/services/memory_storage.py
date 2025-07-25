import threading
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from app.database.connection import sync_engine
from app.models.database import APIMetric, SystemMetric, APIError, UIError

class TimeWindowedStorage:
    """Thread-safe time-windowed storage for metrics"""
    
    def __init__(self, max_age_minutes: int = 120):
        self.max_age = timedelta(minutes=max_age_minutes)
        self.data = deque()
        self.lock = threading.Lock()
    
    def add(self, item: Dict[str, Any]):
        """Add item with current timestamp"""
        with self.lock:
            # Add timestamp if not present
            if 'timestamp' not in item:
                item['timestamp'] = datetime.utcnow().isoformat()
            
            self.data.append(item)
            self._cleanup_old_data()
    
    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get most recent items"""
        with self.lock:
            self._cleanup_old_data()
            return list(self.data)[-limit:]
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all items in window"""
        with self.lock:
            self._cleanup_old_data()
            return list(self.data)
    
    def _cleanup_old_data(self):
        """Remove items older than max_age"""
        cutoff_time = datetime.utcnow() - self.max_age
        
        while self.data:
            try:
                # Parse timestamp from first item
                timestamp_str = self.data[0].get('timestamp')
                if timestamp_str:
                    item_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if item_time < cutoff_time:
                        self.data.popleft()
                    else:
                        break
                else:
                    # Remove items without timestamp
                    self.data.popleft()
            except (ValueError, TypeError):
                # Remove items with invalid timestamp
                self.data.popleft()

class MemoryStorage:
    """Central in-memory storage for all metrics"""
    
    def __init__(self):
        # Initialize database session
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        
        # Time-windowed storage for different metric types
        self.api_metrics = TimeWindowedStorage(max_age_minutes=120)  # 2 hours
        self.system_metrics = TimeWindowedStorage(max_age_minutes=60)  # 1 hour
        self.api_errors = TimeWindowedStorage(max_age_minutes=240)  # 4 hours
        self.ui_errors = TimeWindowedStorage(max_age_minutes=240)  # 4 hours
        
        # Aggregated statistics (updated in real-time)
        self.aggregated_stats = {
            "api_stats": {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "error_count": 0,
                "requests_per_minute": 0.0
            },
            "system_stats": {
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "latest_metrics": None
            },
            "ui_stats": {
                "total_errors": 0,
            }
        }
        self.stats_lock = threading.Lock()
        
        # Load existing data from database
        self._load_from_database()
    
    def _load_from_database(self):
        """Load recent metrics from database into memory storage"""
        try:
            db = self.SessionLocal()
            
            # Load API metrics from last 2 hours
            cutoff_time = datetime.utcnow() - timedelta(minutes=120)
            api_metrics = db.query(APIMetric).filter(
                APIMetric.timestamp >= cutoff_time
            ).order_by(desc(APIMetric.timestamp)).all()
            
            for metric in api_metrics:
                metric_data = {
                    'timestamp': metric.timestamp.isoformat(),
                    'data': {
                        'method': metric.method,
                        'path': metric.path,
                        'status_code': metric.status_code,
                        'response_time_ms': metric.response_time_ms,
                        'success': metric.success
                    }
                }
                self.api_metrics.add(metric_data)
            
            # Load system metrics from last 1 hour
            cutoff_time = datetime.utcnow() - timedelta(minutes=60)
            system_metrics = db.query(SystemMetric).filter(
                SystemMetric.timestamp >= cutoff_time
            ).order_by(desc(SystemMetric.timestamp)).all()
            
            for metric in system_metrics:
                metric_data = {
                    'timestamp': metric.timestamp.isoformat(),
                    'data': {
                        'cpu_percent': metric.cpu_percent,
                        'memory_percent': metric.memory_percent,
                        'disk_usage': metric.disk_usage,
                        'process_memory': metric.process_memory
                    }
                }
                self.system_metrics.add(metric_data)
            
            # Load API errors from last 4 hours
            cutoff_time = datetime.utcnow() - timedelta(minutes=240)
            api_errors = db.query(APIError).filter(
                APIError.timestamp >= cutoff_time
            ).order_by(desc(APIError.timestamp)).all()
            
            for error in api_errors:
                error_data = {
                    'timestamp': error.timestamp.isoformat(),
                    'data': {
                        'error_type': error.error_type,
                        'error_message': error.error_message,
                        'additional_data': error.additional_data
                    }
                }
                self.api_errors.add(error_data)
            
            # Load UI errors from last 4 hours
            cutoff_time = datetime.utcnow() - timedelta(minutes=240)
            ui_errors = db.query(UIError).filter(
                UIError.timestamp >= cutoff_time
            ).order_by(desc(UIError.timestamp)).all()
            
            for error in ui_errors:
                error_data = {
                    'timestamp': error.timestamp.isoformat(),
                    'data': {
                        'error_type': error.error_type,
                        'error_message': error.error_message,
                        'user_id': error.user_id,
                        'additional_data': error.additional_data
                    }
                }
                self.ui_errors.add(error_data)
            
            # Update aggregated statistics
            self._update_api_stats()
            self._update_system_stats()
            self._update_ui_stats()
            
        except Exception as e:
            print(f"Error loading data from database: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def add_api_metric(self, metric: Dict[str, Any]):
        """Add API metric and update stats"""
        self.api_metrics.add(metric)
        self._update_api_stats()
    
    def add_system_metric(self, metric: Dict[str, Any]):
        """Add system metric and update stats"""
        self.system_metrics.add(metric)
        self._update_system_stats()
    
    def add_api_error(self, error: Dict[str, Any]):
        """Add custom event"""
        self.api_errors.add(error)
    
    def add_ui_error(self, error: Dict[str, Any]):
        """Add frontend error and update stats"""
        self.ui_errors.add(error)
        self._update_ui_stats()
    
    def _update_api_stats(self):
        """Update aggregated API statistics"""
        with self.stats_lock:
            api_data = self.api_metrics.get_all()
            
            if not api_data:
                return
            
            # Extract data field from each metric
            metrics = [item.get('data', {}) for item in api_data if 'data' in item]
            
            if not metrics:
                return
            
            total_requests = len(metrics)
            successful_requests = sum(1 for m in metrics if m.get('success', False))
            response_times = [m.get('response_time_ms', 0) for m in metrics]
            
            # Calculate requests per minute (last 10 minutes)
            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
            recent_metrics = [
                item for item in api_data 
                if datetime.fromisoformat(item.get('timestamp', '').replace('Z', '+00:00')) > ten_minutes_ago
            ]
            requests_per_minute = len(recent_metrics) / 10.0
            
            self.aggregated_stats["api_stats"] = {
                "total_requests": total_requests,
                "success_rate": round((successful_requests / total_requests * 100), 2) if total_requests > 0 else 0,
                "avg_response_time": round(sum(response_times) / len(response_times), 2) if response_times else 0,
                "error_count": total_requests - successful_requests,
                "requests_per_minute": round(requests_per_minute, 2)
            }
    
    def _update_system_stats(self):
        """Update aggregated system statistics"""
        with self.stats_lock:
            system_data = self.system_metrics.get_recent(10)  # Last 10 readings
            
            if not system_data:
                return
            
            metrics = [item.get('data', {}) for item in system_data if 'data' in item]
            
            if not metrics:
                return
            
            cpu_values = [m.get('cpu_percent', 0) for m in metrics]
            memory_values = [m.get('memory_percent', 0) for m in metrics]
            
            self.aggregated_stats["system_stats"] = {
                "avg_cpu": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
                "avg_memory": round(sum(memory_values) / len(memory_values), 2) if memory_values else 0,
                "latest_metrics": system_data[-1] if system_data else None
            }
    
    def _update_ui_stats(self):
        """Update aggregated UI statistics"""
        with self.stats_lock:
            errors = self.ui_errors.get_all()
            
            total_errors = len(errors)
            
            self.aggregated_stats["ui_stats"] = {
                "total_errors": total_errors,
            }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data for dashboard"""
        return {
            "aggregated": self.aggregated_stats.copy(),
            "recent_api_metrics": self.api_metrics.get_recent(20),
            "recent_system_metrics": self.system_metrics.get_recent(10),
            "recent_api_errors": self.api_errors.get_recent(10),
            "recent_ui_errors": self.ui_errors.get_recent(10),
        }

# Global memory storage instance
memory_storage = MemoryStorage()