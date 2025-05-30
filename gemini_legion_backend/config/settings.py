"""
Configuration Management

Handles all configuration for the Gemini Legion backend.
"""

from pydantic import BaseSettings, Field
from typing import Optional, List, Dict
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Gemini Legion Backend"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./gemini_legion.db",
        env="DATABASE_URL"
    )
    
    # Redis (for caching)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # API Keys (stored securely)
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # File paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = Field(default=None)
    logs_dir: Path = Field(default=None)
    diary_storage_path: Path = Field(default=None)
    
    # Minion defaults
    default_model: str = Field(default="gemini-1.5-flash", env="DEFAULT_MODEL")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=4096, env="DEFAULT_MAX_TOKENS")
    
    # Communication settings
    max_messages_per_minute: int = Field(default=10, env="MAX_MESSAGES_PER_MINUTE")
    max_messages_per_hour: int = Field(default=60, env="MAX_MESSAGES_PER_HOUR")
    turn_cooldown_seconds: float = Field(default=2.0, env="TURN_COOLDOWN_SECONDS")
    
    # Safety settings
    max_minions: int = Field(default=20, env="MAX_MINIONS")
    max_channels: int = Field(default=50, env="MAX_CHANNELS")
    message_history_limit: int = Field(default=1000, env="MESSAGE_HISTORY_LIMIT")
    
    # Emotional engine settings
    max_mood_change_per_interaction: float = Field(default=0.3, env="MAX_MOOD_CHANGE")
    max_opinion_change_per_interaction: float = Field(default=25.0, env="MAX_OPINION_CHANGE")
    emotional_decay_rate: float = Field(default=0.95, env="EMOTIONAL_DECAY_RATE")
    
    # Memory settings
    working_memory_capacity: int = Field(default=7, env="WORKING_MEMORY_CAPACITY")
    episodic_memory_threshold: float = Field(default=0.5, env="EPISODIC_MEMORY_THRESHOLD")
    memory_consolidation_interval_hours: int = Field(default=24, env="MEMORY_CONSOLIDATION_INTERVAL")
    
    # Task settings
    default_task_timeout_seconds: int = Field(default=300, env="DEFAULT_TASK_TIMEOUT")
    max_concurrent_tasks_per_minion: int = Field(default=3, env="MAX_CONCURRENT_TASKS")
    
    # Feature flags
    enable_autonomous_messaging: bool = Field(default=True, env="ENABLE_AUTONOMOUS_MESSAGING")
    enable_inter_minion_chat: bool = Field(default=True, env="ENABLE_INTER_MINION_CHAT")
    enable_emotional_decay: bool = Field(default=True, env="ENABLE_EMOTIONAL_DECAY")
    enable_memory_consolidation: bool = Field(default=False, env="ENABLE_MEMORY_CONSOLIDATION")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set derived paths
        if not self.data_dir:
            self.data_dir = self.base_dir / "data"
        if not self.logs_dir:
            self.logs_dir = self.base_dir / "logs"
        if not self.diary_storage_path:
            self.diary_storage_path = self.data_dir / "diaries"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.diary_storage_path.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
