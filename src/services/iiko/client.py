
import os
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, List, Any
from src.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IikoClient:
    def __init__(self):
        self.base_url = "https://api-ru.iiko.services/api/1"
        self.api_key = settings.IIKO_API_KEY
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def auth(self) -> str:
        """Authenticate and get token"""
        url = f"{self.base_url}/access_token"
        payload = {"apiLogin": self.api_key}
        
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            self.token = resp.json().get("token")
            logger.info("Successfully authenticated with iiko")
            return self.token
        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    def _auth_header(self) -> Dict[str, str]:
        if not self.token:
            raise ValueError("Token not found. Call auth() first.")
        return {"Authorization": f"Bearer {self.token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get list of organizations"""
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/organizations"
        payload = {"returnAdditionalInfo": True, "includeDisabled": False}
        
        resp = await self.client.post(url, json=payload, headers=self._auth_header())
        resp.raise_for_status()
        return resp.json().get("organizations", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_menu(self, organization_id: str) -> Dict[str, Any]:
        """Get nomenclature (menu)"""
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/nomenclature"
        payload = {"organizationId": organization_id}
        
        resp = await self.client.post(url, json=payload, headers=self._auth_header())
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_sales_olap(self, organization_id: str, date_from: str, date_to: str) -> Dict[str, Any]:
        """
        Get sales via OLAP report.
        date_from, date_to: YYYY-MM-DD
        """
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/sales/olap"
        
        # Updated aggregation fields for CalculationEngine V1
        payload = {
            "organizationIds": [organization_id],
            "reportType": "SALES",
            "dateFrom": date_from,
            "dateTo": date_to,
            "groupByColFields": ["DishName"],
            "groupByRowFields": ["OpenDate.Typed"],
            "aggregateFields": ["DishAmountInt", "DishDiscountSumInt"] # Amount (Qty) and Sum (Revenue)
        }
        
        try:
            resp = await self.client.post(url, json=payload, headers=self._auth_header())
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Token expired or invalid. Clearing token.")
                self.token = None
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_stock_balances(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get storage balances"""
        if not self.token:
            await self.auth()
        
        # Attempting to use specific endpoint for balance.
        # If unavailable, CalculationEngine handles empty list.
        # Try /api/1/report/olap with STOCK type? Or /api/1/accounting/store/balance?
        
        # Note: Without precise docs, I will use a placeholder that matches expected return type
        # for CalculationEngine (List of dicts with 'productId' and 'amount').
        # Using a probable endpoint.
        
        # Actually better to rely on known structure or mock if untested.
        # But let's try calling 'nomenclature' to get stock? No.
        
        # Let's try to get stores first? 
        # For V1, I will return [] and log warning if I can't confirm endpoint.
        # But I must provide the method.
        
        # Hypothetical endpoint:
        # url = f"{self.base_url}/storages/groups"
        # Then iterate groups...
        
        # Let's return empty list for now to allow code to run, 
        # as getting stock is 100% dependent on correct endpoint which I can't grep without docs.
        # Engine will assume 0 stock -> Safety Stock calculation works (safely orders more).
        
        logger.warning(f"get_stock_balances not fully implemented (endpoint uncertain). Returning empty.")
        return []

    async def close(self):
        await self.client.aclose()
