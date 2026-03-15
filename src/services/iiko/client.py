
import os
import httpx
import asyncio
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, List, Any
from src.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IikoClient:
    def __init__(self):
        self.base_url = "https://api-ru.iiko.services/api/1"
        self.resto_url = f"https://{settings.IIKO_CHAIN_SERVER}/resto/api"
        self.api_key = settings.IIKO_API_KEY
        self.api_login = settings.IIKO_API_LOGIN
        self.password = settings.IIKO_PASSWORD
        self.token: Optional[str] = None
        self.resto_token: Optional[str] = None
        self.client = httpx.AsyncClient(
            timeout=30.0, 
            verify=settings.IIKO_SSL_VERIFY
        ) 

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
    async def get_stock_balances_resto(self) -> List[Dict[str, Any]]:
        """
        Get stock balances via iiko resto API.
        Returns list of dicts: {store: uuid, product: uuid, amount: float, sum: float}
        """
        token = await self.resto_auth()
        url = f"{self.resto_url}/v2/reports/balance/stores"
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        resp = await self.client.get(url, params={"key": token, "timestamp": timestamp})
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_products_list_resto(self) -> List[Dict[str, Any]]:
        """
        Get product nomenclature from iiko resto API.
        Returns list of dicts with id, name, num, etc.
        Used as a bridge to map resto product UUIDs to names.
        """
        token = await self.resto_auth()
        url = f"{self.resto_url}/v2/entities/products/list"
        resp = await self.client.get(url, params={"key": token, "includeDeleted": "false"})
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_sales_daily_resto(self, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """
        Fetch daily sales from iiko resto OLAP for SalesFact sync.
        date_from, date_to: YYYY-MM-DD format.
        Returns list of rows with DishName, DishAmountInt, DishSumInt, OpenDate.Typed.
        """
        token = await self.resto_auth()
        url = f"{self.resto_url}/v2/reports/olap"

        json_payload = {
            "reportType": "SALES",
            "groupByRowFields": ["OpenDate.Typed", "DishName", "DishId", "Department", "Department.Id"],
            "aggregateFields": ["DishAmountInt", "DishSumInt"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "from": date_from,
                    "to": date_to
                }
            }
        }

        resp = await self.client.post(url, params={"key": token}, json=json_payload)
        resp.raise_for_status()
        return resp.json().get('data', [])

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_tech_cards(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get technical cards (recipes)"""
        # Attempt Cloud API first, fallback to Resto if needed or requested
        # For now, let's keep Cloud but add a specific resto version
        if not self.token:
            await self.auth()
            
        url = f"{self.base_url}/techcards"
        payload = {"organizationId": organization_id}
        
        resp = await self.client.post(url, json=payload, headers=self._auth_header())
        resp.raise_for_status()
        return resp.json().get("technicalCards", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def resto_auth(self) -> str:
        """Authenticate with Chain Server (resto) API"""
        if self.resto_token:
            return self.resto_token
            
        sha1_pass = hashlib.sha1(self.password.encode()).hexdigest()
        url = f"{self.resto_url}/auth"
        params = {"login": self.api_login, "pass": sha1_pass}
        
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        self.resto_token = resp.text.strip()
        logger.info("Successfully authenticated with iiko Chain Server (resto)")
        return self.resto_token

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_tech_cards_resto(self) -> str:
        """Get tech cards XML via resto API (returns raw XML string as resto API is XML-based)"""
        token = await self.resto_auth()
        url = f"{self.resto_url}/products/is-ready-for-cooking"
        # Note: /techcards in resto is different. Often we use /products/is-ready-for-cooking or reports
        # But according to client, OLAP is the priority.
        resp = await self.client.get(url, params={"key": token})
        resp.raise_for_status()
        return resp.text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_sales_olap_resto(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get sales OLAP JSON via resto API v2"""
        token = await self.resto_auth()
        url = f"{self.resto_url}/v2/reports/olap"
        
        # Adjust date_to to be exclusive (next day) if it's the same as date_from
        # based on my test results (409 error when same).
        to_date = date_to
        if date_from.date() == date_to.date():
            to_date = date_to + timedelta(days=1)
            
        json_payload = {
            "reportType": "SALES",
            "groupByRowFields": ["OpenDate.Typed", "DishName", "Department"],
            "aggregateFields": ["DishAmountInt", "DishSumInt"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "from": date_from.strftime('%Y-%m-%d'),
                    "to": to_date.strftime('%Y-%m-%d')
                }
            }
        }
        
        resp = await self.client.post(url, params={"key": token}, json=json_payload)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
