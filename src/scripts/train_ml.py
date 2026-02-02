
import asyncio
import logging
from src.services.ml.forecast_service import ForecastService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting ML Training Pipeline...")
    service = ForecastService()
    try:
        service.train_model()
        logger.info("Training completed successfully.")
        
        # Test Prediction
        test_plan = 60000
        mult = service.predict_usage(test_plan)
        logger.info(f"Test Prediction for {test_plan} RUB: Multiplier = {mult:.3f}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")

if __name__ == "__main__":
    main()
