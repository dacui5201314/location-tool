from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def analyze(self, prompt: str) -> str:
        """Send prompt to AI and return response text."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...
