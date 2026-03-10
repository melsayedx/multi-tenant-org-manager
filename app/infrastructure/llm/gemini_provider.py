from typing import AsyncIterator

import google.genai as genai

from app.config import settings

_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=_MODEL, contents=prompt
        )
        return response.text

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=_MODEL, contents=prompt
        ):
            if chunk.text:
                yield chunk.text
