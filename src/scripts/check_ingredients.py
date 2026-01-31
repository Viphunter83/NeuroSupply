
import asyncio
import logging
from src.db.session import async_session_maker
from src.db.models.product import Product
from sqlalchemy import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Checking Ingredients in DB...")
    
    async with async_session_maker() as session:
        result = await session.execute(select(Product).where(Product.category == "Ingredient"))
        ingredients = result.scalars().all()
        
        logger.info(f"Total Ingredients: {len(ingredients)}")
        
        with_package = [p for p in ingredients if p.package_size is not None]
        logger.info(f"Ingredients with parsed Package Size: {len(with_package)}")
        
        if with_package:
            logger.info("Sample with Package:")
            p = with_package[0]
            logger.info(f"Name: {p.name_ru} | Pkg: {p.package_size} {p.package_unit}")
        else:
            logger.warning("No package sizes parsed! Check regex or data.")

if __name__ == "__main__":
    asyncio.run(main())
