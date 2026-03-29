from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "DBA-Sentinel"
    VERSION: str = "1.0.0"
    
    # API Security
    API_SECRET_KEY: str = "supersecret_dba_key"
    
    # Notificaciones
    SLACK_WEBHOOK_URL: str = ""
    EMAIL_SMTP_SERVER: str = ""
    EMAIL_ADMIN_ADDRESS: str = ""
    
    # DB Credentials (Ejemplo genérico, en prod cada motor tendrá sus credenciales)
    PG_USER: str = "postgres"
    PG_PASSWORD: str = ""
    PG_HOST: str = "localhost"
    PG_PORT: str = "5432"
    PG_DB: str = "postgres"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
