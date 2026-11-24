from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    system_prompt: str = "You are an assitant for Care Compass, as users chat with you, your job is to guide them to tell you their symptoms until you have enough information to place them in the pain-druation-scale. The PDS is cooridinate system where x is the level of pain 0-10 and y is the duration in days."
    session_ttl: int = 60 * 30  # seconds of idle time before a session is dropped


@lru_cache
def get_settings() -> Settings:
    return Settings()