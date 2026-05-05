import httpx
from .base import BaseProvider
from config import ZHIPU_API_KEY, PROVIDER_CONFIG


class ZhipuProvider(BaseProvider):
    name = "zhipu"

    async def analyze(self, prompt: str) -> str:
        config = PROVIDER_CONFIG["zhipu"]
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {ZHIPU_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
