from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIMetric(Base):
    __tablename__ = "api_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    method = Column(String(10))
    path = Column(String(255))
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    success = Column(Boolean)

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_usage = Column(Float)
    process_memory = Column(Float)

class APIError(Base):
    __tablename__ = "api_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    error_type = Column(String(100))
    error_message = Column(Text)
    additional_data = Column(Text, nullable=True)  # JSON string

class UIError(Base):
    __tablename__ = "ui_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    error_type = Column(String(100))
    error_message = Column(Text)
    user_id = Column(String(100), nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON string