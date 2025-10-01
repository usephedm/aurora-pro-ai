"""
Aurora Pro AI - Configuration Management
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "aurora-pro-ai"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_host: str = "0.0.0.0"
    streamlit_port: int = 8501
    
    # Database
    database_url: str = "sqlite:///./data/aurora.db"
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI/LLM
    ollama_base_url: str = "http://ollama:11434"
    openai_api_key: str = ""
    default_model: str = "llama2"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Multi-Agent
    max_agents: int = 10
    agent_timeout: int = 300
    orchestration_mode: str = "sequential"
    
    # Browser Automation
    playwright_browsers_path: str = "/ms-playwright"
    headless_browser: bool = True
    
    # Monitoring
    prometheus_port: int = 9090
    metrics_enabled: bool = True
    health_check_interval: int = 30
    
    # Celery
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8501"]
    
    # Plugin System
    plugins_enabled: bool = True
    plugins_dir: str = "/app/plugins"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
