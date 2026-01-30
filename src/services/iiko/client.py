import httpx
from typing import Optional, Dict, Any, List
from src.core.config import settings

class IikoClient:
    BASE_URL = "https://api-ru.iiko.services/api/1"

    def __init__(self):
        self.api_login = settings.IIKO_API_LOGIN
        self.token: Optional[str] = None

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        if not self.token and endpoint != "/access_token":
            await self.authenticate()
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}{endpoint}"
            response = await client.request(method, url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def authenticate(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/access_token", 
                json={"apiLogin": self.api_login}
            )
            resp.raise_for_status()
            self.token = resp.json().get("token")
            return self.token

    async def get_organizations(self) -> Dict[str, Any]:
        return await self._make_request("POST", "/organizations", {})

    async def get_menu(self, organization_id: str) -> Dict[str, Any]:
        return await self._make_request("POST", "/nomenclature", {
            "organizationId": organization_id,
            "startRevision": 0
        })

    async def get_terminal_groups(self, organization_ids: List[str]) -> Dict[str, Any]:
        return await self._make_request("POST", "/terminal_groups", {
            "organizationIds": organization_ids,
            "includeDisabled": False
        })
