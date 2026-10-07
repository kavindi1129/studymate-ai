"""Common AI provider contract for StudyMate AI."""

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """Base class for provider failures with a student-friendly message."""


class ProviderAuthError(ProviderError):
    """The API key is missing or invalid."""


class ProviderConnectionError(ProviderError):
    """The provider could not be reached (bad base URL / network)."""


class ProviderModelError(ProviderError):
    """The configured model name could not be used."""


class ProviderUnavailableError(ProviderError):
    """The provider is temporarily unavailable or over its usage limit."""


class AIProvider(ABC):
    """Every StudyMate AI provider implements this single operation."""

    def __init__(self, name: str, model: str) -> None:
        self.name = name
        self.model = model

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        json_mode: bool = False,
    ) -> str:
        """Send one prompt to the model and return the generated text.

        json_mode asks for a raw JSON response where the provider supports it
        natively; providers without a JSON mode rely on the prompt instead.
        """
