from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ML Settings
    DEFAULT_ML_BASE_NORM: float = 0.0015 # Expected usage per 1 RUB of revenue
    
    # Calculation Settings
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
    IIKO_SSL_VERIFY: bool = False # Default to False for now, but configurable
    
    PROCOB_API_KEY: str = "" # For future integration
    
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = ""
    
    SUPABASE_JWT_SECRET: str
    
    # Custom JWT Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # AI (OpenAI / ProxyAPI)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"

    # CORS
    CORS_ORIGINS: str = "*"

    # Feature Flags
    USE_MOCK_DATA: bool = False
    DEMO_RESTAURANT_ID: str = "00000000-0000-0000-0000-000000000000"
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
