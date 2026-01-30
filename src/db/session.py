from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings

engine = create_async_engine(str(settings.PG_DSN), echo=settings.APP_ENV == "development")
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
