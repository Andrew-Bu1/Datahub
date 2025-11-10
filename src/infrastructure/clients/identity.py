from logging import Logger, getLogger

import httpx

from src.configurations import Settings


class IdentityClient:
    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings
        self.logger: Logger = getLogger(__name__)

    async def get_token(self) -> str:
        try:
            payload: dict[str, str] = {
                "Name": self.settings.identity_user,
                "Secret": self.settings.identity_secret,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.settings.identity_url}", json=payload)
                response.raise_for_status()
                return response.json()["accessToken"]
        except httpx.HTTPError as e:
            self.logger.error(f"Failed to retrieve access token: {e}")
            raise e
