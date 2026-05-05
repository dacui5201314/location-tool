import httpx
from .base import BaseProvider
from config import GEMINI_API_KEY, PROVIDER_CONFIG


class GeminiProvider(BaseProvider):
    name = "gemini"

    async def analyze(self, prompt: str) -> str:
        config = PROVIDER_CONFIG["gemini"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={GEMINI_API_KEY}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
