from typing import AsyncIterator, Protocol


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Generate a complete response."""
        ...

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response chunks."""
        ...
