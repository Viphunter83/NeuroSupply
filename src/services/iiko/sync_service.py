import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.iiko.client import IikoClient
from src.db.models import Product, StockBalance, EmpiricalRecipe, Restaurant

logger = logging.getLogger(__name__)

class IikoSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.iiko = IikoClient()

    async def sync_stock_balances(self, restaurant_id: uuid.UUID):
        """
        Syncs stock balances for a specific restaurant directly from iiko resto API.
        Uses atomic deletion within the same transaction to minimize zero-stock window.
        """
        logger.info(f"Starting stock sync for restaurant {restaurant_id}")
        
        # 1. Fetch from iiko
        balances = await self.iiko.get_stock_balances_resto()
        
        # 2. Map iiko products to our DB Products
        stmt = select(Product)
        result = await self.db.execute(stmt)
        products = result.scalars().all()
        p_map = {p.iiko_id: p.id for p in products}

        # 3. Use transaction for atomic swap
        # We perform delete and insert in the same commit block
        await self.db.execute(delete(StockBalance).where(StockBalance.restaurant_id == restaurant_id))
        
        count = 0
        for b in balances:
            p_iiko_id = b.get("product")
            if p_iiko_id in p_map:
                new_balance = StockBalance(
                    restaurant_id=restaurant_id,
                    product_id=p_map[p_iiko_id],
                    amount=float(b.get("amount", 0)),
                    snapshot_at=datetime.now(timezone.utc)
                )
                self.db.add(new_balance)
                count += 1
        
        await self.db.commit()
        logger.info(f"Synced {count} stock balance records for restaurant {restaurant_id}")

    async def sync_recipes(self, restaurant_id: uuid.UUID):
        """
        Syncs technical cards (recipes) from iiko Cloud API.
        """
        stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await self.db.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        if not restaurant or not restaurant.iiko_id:
            logger.error(f"Restaurant {restaurant_id} not found or has no iiko_id")
            return

        logger.info(f"Starting recipe sync for iiko org {restaurant.iiko_id}")
        
        # 1. Fetch tech cards from Cloud API
        # get_tech_cards returns list of technical cards
        cards = await self.iiko.get_tech_cards(str(restaurant.iiko_id))
        
        # 2. Map Products
        stmt_p = select(Product)
        result_p = await self.db.execute(stmt_p)
        p_map = {p.iiko_id: p.id for p in result_p.scalars().all()}

        # 3. Process Cards
        # For simplicity, we skip existing delete for recipes for now or handle updates.
        # Let's clear EmpiricalRecipe for this restaurant if we can identify them.
        # Actually EmpiricalRecipe doesn't have restaurant_id yet? Let's check model.
        # line 39 of analytics.py defines EmpiricalRecipe: dish_id, dish_name, ingredient_name, product_id, yield_rate
        # It's global currently? Or restaurant-specific? 
        # In multi-tenant, it should be restaurant-specific or global if shared.
        # Assuming global for now as per model.
        
        count = 0
        for card in cards:
            dish_id = card.get("id")
            dish_name = card.get("name")
            
            ingredients = card.get("ingredients", [])
            for ing in ingredients:
                ing_product_id = ing.get("productId")
                ing_amount = ing.get("amount", 0)
                
                my_p_id = p_map.get(ing_product_id)
                
                # Update or create EmpiricalRecipe (Isolated by restaurant_id)
                stmt_r = select(EmpiricalRecipe).where(
                    EmpiricalRecipe.restaurant_id == restaurant_id,
                    EmpiricalRecipe.dish_name == dish_name,
                    EmpiricalRecipe.ingredient_name == ing.get("productName")
                )
                res_r = await self.db.execute(stmt_r)
                existing = res_r.scalar_one_or_none()
                
                if existing:
                    existing.yield_rate = float(ing_amount)
                    existing.product_id = my_p_id
                    existing.dish_id = uuid.UUID(dish_id) if dish_id else None
                else:
                    new_recipe = EmpiricalRecipe(
                        restaurant_id=restaurant_id,
                        dish_id=uuid.UUID(dish_id) if dish_id else None,
                        dish_name=dish_name,
                        ingredient_name=ing.get("productName"),
                        product_id=my_p_id,
                        yield_rate=float(ing_amount)
                    )
                    self.db.add(new_recipe)
                count += 1
        
        await self.db.commit()
        logger.info(f"Synced {count} recipe records")
