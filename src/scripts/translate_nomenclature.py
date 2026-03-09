"""
Mass translate product nomenclature from name_ru to name_vn using OpenAI (ProxyAPI).
Only translates products where name_vn is NULL or empty.
"""
import asyncio
import logging
import json
from typing import List, Dict
import httpx

from sqlalchemy import select
from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models.product import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def translate_batch(batch: List[Product]) -> Dict[str, str]:
    """Sends a batch of Russian names to OpenAI and returns a mapping {ru_name: vn_name}."""
    if not batch:
        return {}

    names = [p.name_ru for p in batch]
    
    prompt = (
        "Translate the following restaurant and grocery items from Russian to Vietnamese. "
        "Maintain culinary accuracy. Output a JSON object where keys are Russian names and values are Vietnamese translations.\n\n"
        "Items:\n" + "\n".join(f"- {name}" for name in names)
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional culinary translator (Russian to Vietnamese)."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if resp.status_code != 200:
                logger.error(f"OpenAI API error ({resp.status_code}): {resp.text}")
                return {}
            
            result_json = resp.json()
            content = result_json['choices'][0]['message']['content']
            translations = json.loads(content)
            
            # Clean up keys if they have the '- ' prefix
            cleaned_translations = {}
            for k, v in translations.items():
                clean_k = k.lstrip("- ").strip()
                cleaned_translations[clean_k] = v
                
            return cleaned_translations

    except Exception as e:
        logger.error(f"Translation request failed: {e}")
        return {}

async def main():
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in settings.")
        return

    logger.info("🚀 Starting nomenclature translation...")
    
    async with async_session_maker() as session:
        # 1. Fetch products needing translation
        stmt = select(Product).where((Product.name_vn == None) | (Product.name_vn == ""))
        result = await session.execute(stmt)
        products_to_translate = result.scalars().all()
        
        total = len(products_to_translate)
        if total == 0:
            logger.info("✅ All products already have Vietnamese names.")
            return
            
        logger.info(f"Found {total} items to translate.")
        
        batch_size = 25
        for i in range(0, total, batch_size):
            batch = products_to_translate[i : i + batch_size]
            logger.info(f"Translating batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}...")
            
            mapping = await translate_batch(batch)
            
            success_count = 0
            for p in batch:
                # Try exact match, then stripped match
                vn_name = mapping.get(p.name_ru) or mapping.get(p.name_ru.strip())
                if vn_name:
                    p.name_vn = vn_name
                    success_count += 1
            
            await session.commit()
            logger.info(f"Batch completed: {success_count}/{len(batch)} translated.")
            
            # Small delay to avoid rate limits if any
            await asyncio.sleep(1)

    logger.info("✅ Translation process finished.")

if __name__ == "__main__":
    asyncio.run(main())
