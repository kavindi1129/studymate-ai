"""Gemini provider backed by the google-genai SDK."""

import time

from google import genai
from google.genai import types

from .base import (
    AIProvider,
    ProviderAuthError,
    ProviderError,
    ProviderModelError,
    ProviderUnavailableError,
)

RETRIES = 4  # total attempts for transient overload errors
RETRY_WAIT_SECONDS = 5
REQUEST_TIMEOUT_MS = 120_000  # bound requests so a hanging model fails loudly


class GeminiProvider(AIProvider):
    """Calls the Gemini API, retrying transient server overload errors."""

    def __init__(self, name: str, model: str, api_key: str) -> None:
        super().__init__(name, model)
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        json_mode: bool = False,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )

        attempt = 1
        while True:
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""
            except Exception as exc:
                text = str(exc)
                if not _is_transient(text):
                    raise _friendly_error(exc, text) from exc
                if attempt >= RETRIES:
                    raise ProviderUnavailableError(
                        "Gemini's servers are very busy right now. This is usually "
                        "temporary — please wait a minute and try again."
                    ) from exc
                time.sleep(RETRY_WAIT_SECONDS)
                attempt += 1


def _is_transient(text: str) -> bool:
    return "high demand" in text or "UNAVAILABLE" in text


def _friendly_error(exc: Exception, text: str) -> ProviderError:
    """Translate a Gemini SDK error into a student-friendly message."""
    if (
        "API key not valid" in text
        or "API_KEY_INVALID" in text
        or "PERMISSION_DENIED" in text
    ):
        return ProviderAuthError(
            "Authentication failed. Please check your Gemini API key "
            "(GEMINI_API_KEY in the .env file)."
        )
    if "timed out" in text.lower() or "timeout" in text.lower():
        return ProviderUnavailableError(
            "Gemini is not responding right now. Please try again, or switch "
            "to a different model in Settings."
        )
    if "quota" in text.lower() or "RESOURCE_EXHAUSTED" in text:
        return ProviderUnavailableError(
            "The Gemini API is busy or over its usage limit. "
            "Please wait a moment and try again."
        )
    if "404" in text or "NOT_FOUND" in text or "not found" in text.lower():
        return ProviderModelError(
            "The selected Gemini model could not be used. "
            "Please check the model name in Settings."
        )
    return ProviderError(
        "Could not reach the Gemini API. Check your internet "
        "connection and try again."
    )
