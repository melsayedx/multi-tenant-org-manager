from typing import AsyncIterator, Protocol


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Single-turn: generate a complete response."""
        ...

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Single-turn: stream response chunks."""
        ...

    async def chat(self, history: list[dict], message: str) -> str:
        """Multi-turn: continue a conversation given prior history."""
        ...

    async def chat_stream(
        self, history: list[dict], message: str
    ) -> AsyncIterator[str]:
        """Multi-turn: stream response chunks continuing a conversation."""
        ...
