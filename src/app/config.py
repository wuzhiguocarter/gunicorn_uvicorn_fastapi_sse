"""
Configuration settings for the ChatBot SSE Server
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # SSE settings
    sse_keepalive_timeout: int = Field(default=30, env="SSE_KEEPALIVE_TIMEOUT")
    sse_reconnect_delay: int = Field(default=1000, env="SSE_RECONNECT_DELAY")

    # ChatBot settings
    max_history_length: int = Field(default=10, env="MAX_HISTORY_LENGTH")
    response_delay: float = Field(default=0.5, env="RESPONSE_DELAY")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Performance
    max_concurrent_connections: int = Field(default=1000, env="MAX_CONCURRENT_CONNECTIONS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")

    # Security
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")


settings = Settings()