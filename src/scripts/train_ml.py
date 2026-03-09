
import asyncio
import logging
from src.services.ml.forecast_service import ForecastService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting ML Training Pipeline...")
    service = ForecastService()
    from src.db.session import async_session_maker as SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Try to train from DB first (it will fallback to synthetic if not enough data)
            await service.train_from_db(db)
            logger.info("Training completed successfully.")
            
            # Test Prediction
            test_plan = 60000
            mult = service.predict_usage(test_plan)
            logger.info(f"Test Prediction for {test_plan} RUB: Multiplier = {mult:.3f}")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
