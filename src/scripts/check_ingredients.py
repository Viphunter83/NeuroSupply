
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
        # Get count of all products
        all_stmt = select(Product)
        all_res = await session.execute(all_stmt)
        all_prods = all_res.scalars().all()
        logger.info(f"Total Products in DB: {len(all_prods)}")

        # Find ingredients (let's assume any non-dish is an ingredient for diagnostic purposes)
        ingredients = all_prods 
        
        # Show distinct categories
        cats = sorted(list(set(p.category for p in all_prods if p.category)))
        logger.info(f"Distinct Categories: {cats[:10]}... (Total: {len(cats)})")
        
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
