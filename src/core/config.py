from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    
    # Google Integration
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = "secrets/service_account.json"
    GOOGLE_SHEETS_SPREADSHEET_ID: str = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"
    
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
    IIKO_PASSWORD: str = ""
    IIKO_CHAIN_SERVER: str = ""
    IIKO_ORG_ID: str = ""
    
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = ""

    # AI (OpenAI / ProxyAPI)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8090"

    # Feature Flags
    USE_MOCK_DATA: bool = True
    SAFETY_STOCK_RATIO: float = 1.1

    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        return self.BOT_TOKEN

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS_ORIGINS into a list."""
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.WEBAPP_URL:
            origins.append(self.WEBAPP_URL)
        return origins

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
