from typing import AsyncIterator

import google.genai as genai

from app.config import settings

_MODEL = "gemini-3-flash-preview"


class GeminiProvider:
    def __init__(self) -> None:
        # api_key is passed explicitly so the provider works regardless of
        # which environment variable name the caller uses (GEMINI_API_KEY vs GOOGLE_API_KEY).
        self._client = genai.Client(api_key=settings.gemini_api_key)

    # ------------------------------------------------------------------
    # Single-turn
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Multi-turn (chat)
    # ------------------------------------------------------------------

    def _to_gemini_history(self, history: list[dict]) -> list[dict]:
        """Convert plain dicts to the Content format expected by the SDK."""
        return [{"role": h["role"], "parts": [{"text": h["text"]}]} for h in history]

    async def chat(self, history: list[dict], message: str) -> str:
        session = self._client.aio.chats.create(
            model=_MODEL,
            history=self._to_gemini_history(history),
        )
        response = await session.send_message(message)
        return response.text

    async def chat_stream(self, history: list[dict], message: str) -> AsyncIterator[str]:
        session = self._client.aio.chats.create(
            model=_MODEL,
            history=self._to_gemini_history(history),
        )
        # send_message_stream returns an AsyncIterator directly (not a coroutine)
        async for chunk in session.send_message_stream(message):
            if chunk.text:
                yield chunk.text
