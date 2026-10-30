"""
GenVoice 2.0 - Configuration

Loads environment variables and provides configuration settings
"""

# For Pydantic v2
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "sqlite:///./genvoice.db"

    # Twilio SMS (optional - use empty string as default)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # AI Service (optional - use empty string as default)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    RELOAD: bool = True

    # Security
    SECRET_KEY: str = "development_secret_key_change_in_production"
    ALGORITHM: str = "HS256"

    # Feature Flags
    ENABLE_AI_ANALYSIS: bool = True
    ENABLE_SMS_ALERTS: bool = True
    ENABLE_BACKGROUND_JOBS: bool = True

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "GenVoice 2.0 API"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
