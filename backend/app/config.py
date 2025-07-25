from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App settings
    app_name: str = "AppPulse Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # AI Configuration - Choose one
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    google_api_key: Optional[str] = None
    google_model: str = "gemini-1.5-pro"
    
    # Which AI provider to use
    ai_provider: str = "gemini"  # "openai", "claude", or "gemini"
    
    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_auto_offset_reset: str = "earliest"
    
    # Database settings (optional for now)
    database_url: Optional[str] = None
    
    # Metrics settings
    collect_metrics: bool = True
    metrics_sample_rate: float = 1.0
    
    class Config:
        env_file = ".env"

settings = Settings()