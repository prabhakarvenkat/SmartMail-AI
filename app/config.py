from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Model config for loading from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GROQ_API_KEY: str # Changed from OPENAI_API_KEY
    IMAP_SERVER: str
    IMAP_PORT: int
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_ADDRESS: str
    EMAIL_APP_PASSWORD: str
    API_KEY: str

# Instantiate settings to be imported across the application
settings = Settings()