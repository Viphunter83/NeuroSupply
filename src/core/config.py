from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    # Google Integration
    GOOGLE_CREDENTIALS_FILE: str = "secrets/google_credentials.json"
    GOOGLE_SHEET_ID: str = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"
    LOG_LEVEL: str = "INFO"
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    
    PG_DSN: str # Full DSN usually constructed or provided
    
    REDIS_URL: str
    
    IIKO_API_LOGIN: str = ""
    IIKO_API_KEY: str = ""
    IIKO_ORG_ID: str = ""
    
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = ""

    # Feature Flags
    USE_MOCK_DATA: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
