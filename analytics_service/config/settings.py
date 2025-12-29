"""
Configuration settings for Analytics Service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service
    service_name: str = "analytics_service"
    environment: str = "development"

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_consumer_group: str = "analytics_service_group"

    # Kafka Topics
    topic_session_created: str = "practice-session.created"
    topic_answer_submitted: str = "answer.submitted"
    topic_session_completed: str = "session.completed"

    topic_question_generated: str = "question.generated"
    topic_feedback_generated: str = "feedback.generated"
    topic_report_generated: str = "report.generated"

    # Redis
    redis_host: str = "redis-analytics"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None
    redis_ttl: int = 3600  # 1 hour cache TTL

    # AI Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_ai_provider: str = "openai"
    default_model: str = "gpt-4-turbo-preview"

    # Airflow
    airflow_api_url: str = "http://airflow-webserver:8080/api/v1"
    airflow_username: str = "admin"
    airflow_password: str = "admin"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
