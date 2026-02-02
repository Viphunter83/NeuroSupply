
import logging
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from src.core.config import settings

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

    def train_model(self):
        """
        Generates synthetic data and trains a RandomForestRegressor.
        """
        logger.info("Generating synthetic training data...")
        
        # 1. Generate Synthetic Data (3 months)
        # Features: Plan Amount (RUB), Weekday (0-6)
        # Target: Usage Coefficient (base 0.001 + noise)
        
        np.random.seed(42)
        n_days = 90
        
        data = []
        base_date = datetime.now() - timedelta(days=n_days)
        
        for i in range(n_days):
            date = base_date + timedelta(days=i)
            weekday = date.weekday()
            
            # Plan Mock: 30k - 80k, more on weekends
            is_weekend = weekday >= 5
            plan_base = 60000 if is_weekend else 40000
            plan_amount = np.random.normal(plan_base, 5000)
            
            # True Usage Logic (what we want model to learn)
            # Usage is Plan * BaseCoef
            # But BaseCoef varies slightly by day of week
            base_coef = 0.0015 # kg per RUB (abstract)
            if is_weekend:
                base_coef *= 1.1 # More food per ruble on weekends (e.g. cheaper checks?)
            
            # Add noise
            actual_usage = plan_amount * base_coef * np.random.uniform(0.95, 1.05)
            
            data.append({
                "plan_amount": plan_amount,
                "weekday": weekday,
                "usage": actual_usage
            })
            
        df = pd.DataFrame(data)
        
        # 2. Prepare Features & Target
        X = df[["plan_amount", "weekday"]]
        y = df["usage"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 3. Train
        logger.info("Training Forest...")
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # 4. Evaluate
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        logger.info(f"Model Trained. MAE: {mae:.4f}, R2: {r2:.4f}")
        
        # 5. Save
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
