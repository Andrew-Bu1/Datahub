import asyncio
from logging import Logger, getLogger
from typing import Any

import httpx

from src.configurations import Settings
from .identity import IdentityClient

class AiHubClient:
    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings
        self.logger: Logger = getLogger(__name__)

    async def embedding(
        self, 
        inputs: str | list[str], 
        model: str,
        max_retries: int = 3
    ) -> dict[str, Any]:
        """Generate embeddings for text inputs.
        
        Args:
            inputs: Single string or list of strings to embed
            model: Embedding model to use (e.g., 'all-MiniLM-L6-v2')
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with structure:
            {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "embedding": [0.1, 0.2, ...],
                        "index": 0
                    },
                    ...
                ],
                "model": "all-MiniLM-L6-v2",
                "usage": {"prompt_tokens": 0, "total_tokens": 0}
            }
        """
        payload: dict[str, Any] = {
            "inputs": [inputs] if isinstance(inputs, str) else inputs,
            "model": model
        }

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.settings.aihub_url}/embeddings",
                        json=payload,
                    )
                    resp.raise_for_status()
                    return resp.json()

            except Exception as e:
                self.logger.error(
                    f"Unexpected error on attempt {attempt + 1}/{max_retries + 1}: {e}"
                )
                if attempt == max_retries:
                    break

            if attempt < max_retries:
                wait_time = 2**attempt
                self.logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        raise Exception(f"All {max_retries + 1} attempts failed.")
