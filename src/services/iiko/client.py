
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
        # Fixed: Usage of json body instead of params
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
        
        payload = {
            "organizationIds": [organization_id],
            "reportType": "SALES",
            "dateFrom": date_from,
            "dateTo": date_to,
            "groupByColFields": ["DishName"],
            "groupByRowFields": ["OpenDate.Typed"],
            "aggregateFields": ["DishAmountInt", "DishDiscountSumInt"]
        }
        
        try:
            resp = await self.client.post(url, json=payload, headers=self._auth_header())
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning(f"Token expired or invalid: {e.response.text}")
                self.token = None
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_stock_balances(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get storage balances"""
        if not self.token:
            await self.auth()
        
        # Placeholder as endpoint depends on exact business license/modules
        logger.warning(f"get_stock_balances not fully implemented (endpoint uncertain). Returning empty.")
        return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_terminal_groups(self, organization_ids: List[str]) -> List[Dict[str, Any]]:
        """Get terminal groups for organizations"""
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/terminal_groups"
        payload = {"organizationIds": organization_ids}
        
        resp = await self.client.post(url, json=payload, headers=self._auth_header())
        resp.raise_for_status()
        return resp.json().get("terminalGroups", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_stop_lists(self, organization_ids: List[str]) -> List[Dict[str, Any]]:
        """Get out-of-stock items (Stop List)"""
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/stop_lists"
        payload = {"organizationIds": organization_ids}
        
        resp = await self.client.post(url, json=payload, headers=self._auth_header())
        resp.raise_for_status()
        return resp.json().get("terminalGroupStopLists", [])

    async def close(self):
        await self.client.aclose()
