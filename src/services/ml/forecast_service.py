
import logging
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from src.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ForecastService:
    def __init__(self, model_path: str = "src/services/ml/model.pkl"):
        self.model_path = model_path
        self._model = None
        self._load_model()

    def _load_model(self):
        """Loads the trained model if exists."""
        if os.path.exists(self.model_path):
            try:
                self._model = joblib.load(self.model_path)
                logger.info(f"ML Model loaded from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
        else:
            logger.warning("ML Model not found. Predictions will fallback or fail.")

    async def train_from_db(self, db: AsyncSession):
        """
        Fetches real data from SalesFact and trains the model.
        """
        from src.db.models import SalesFact
        from sqlalchemy import select, func

        logger.info("Fetching real training data from database...")
        
        # We need daily revenue and day of week
        stmt = select(
            func.date(SalesFact.date).label("date"),
            func.sum(SalesFact.revenue_rub).label("total_revenue")
        ).group_by(func.date(SalesFact.date)).order_by("date")
        
        result = await db.execute(stmt)
        rows = result.all()
        
        if not rows or len(rows) < 7:
            logger.warning("Not enough real data for training (< 7 days). Falling back to synthetic.")
            self.train_model()
            return

        data = []
        for r in rows:
            # We treat 'total_revenue' as 'plan_amount' for training features 
            # and 'total_revenue' * some_coef as 'usage' for mapping.
            # In a real scenario, 'usage' would be actual ingredient consumption.
            # For MVP, we use revenue as a proxy or fetch Dish Quantity.
            
            # Simplified: Feature = revenue, Target = revenue * base_coef (to learn noise/patterns)
            # Better target: Sum of quantities of all dishes scaled?
            
            d_obj = r.date if isinstance(r.date, date) else datetime.strptime(str(r.date), "%Y-%m-%d").date()
            
            data.append({
                "plan_amount": float(r.total_revenue),
                "weekday": d_obj.weekday(),
                "usage": float(r.total_revenue) * 0.0015 # Placeholder target logic
            })
            
        df = pd.DataFrame(data)
        self._train(df)

    def train_model(self):
        """
        Generates synthetic data and trains a RandomForestRegressor.
        """
        logger.info("Generating synthetic training data...")
        
        np.random.seed(42)
        n_days = 90
        
        data = []
        base_date = datetime.now() - timedelta(days=n_days)
        
        for i in range(n_days):
            date_val = base_date + timedelta(days=i)
            weekday = date_val.weekday()
            
            plan_base = 60000 if weekday >= 5 else 40000
            plan_amount = np.random.normal(plan_base, 5000)
            
            base_coef = 0.0015 
            if weekday >= 5: base_coef *= 1.1 
            
            actual_usage = plan_amount * base_coef * np.random.uniform(0.95, 1.05)
            
            data.append({
                "plan_amount": plan_amount,
                "weekday": weekday,
                "usage": actual_usage
            })
            
        df = pd.DataFrame(data)
        self._train(df)

    def _train(self, df: pd.DataFrame):
        """Internal training logic shared by synthetic and real data paths."""
        X = df[["plan_amount", "weekday"]]
        y = df["usage"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        logger.info(f"Training Forest with {len(df)} samples...")
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        logger.info(f"Model Trained. MAE: {mae:.4f}, R2: {r2:.4f}")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        self._model = model
        logger.info(f"Model saved to {self.model_path}")

    def predict_usage(self, plan_amount: float, date: datetime = None) -> float:
        """
        Predicts total usage (abstract units) for the given plan.
        In reality, we would predict per-category or per-item.
        For MVP, we predict a 'Global Usage Scale' to adjust static norms.
        
        However, to keep it simple for MVP Integration:
        We will return a 'Coefficient' that the Engine can multiply by norms.
        
        If model says usage for 50k is 75kg, and base norm implies 50k -> 0.0015 -> 75kg,
        then coef is 1.0.
        
        Actually, let's just predict the 'Multiplier' for the static norms.
        """
        if not self._model:
            return 1.0 # Fallback
            
        if date is None:
            date = datetime.now()
            
        weekday = date.weekday()
        
        # Predict Usage (Absolute)
        X = pd.DataFrame([[plan_amount, weekday]], columns=["plan_amount", "weekday"])
        predicted_usage = self._model.predict(X)[0]
        
        # We need to map this Absolute Usage back to a Multiplier for our static norms.
        # Let's assume standard static norm expects: Usage = Plan * 0.0015
        expected_standard_usage = plan_amount * 0.0015
        
        if expected_standard_usage == 0:
            return 1.0
            
        multiplier = predicted_usage / expected_standard_usage
        
        # Safety limits
        return max(0.5, min(multiplier, 2.0))
