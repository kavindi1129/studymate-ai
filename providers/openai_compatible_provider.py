"""Generic OpenAI-compatible chat-completions provider.

Talks to any endpoint that implements the OpenAI chat API, so users can
connect any compatible service without hard-coding a vendor.
"""

import requests

from .base import (
    AIProvider,
    ProviderAuthError,
    ProviderConnectionError,
    ProviderError,
    ProviderModelError,
    ProviderUnavailableError,
)

REQUEST_TIMEOUT_SECONDS = 120


class OpenAICompatibleProvider(AIProvider):
    """Sends chat-completions requests over plain HTTP."""

    def __init__(self, name: str, model: str, base_url: str, api_key: str) -> None:
        super().__init__(name, model)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        json_mode: bool = False,
    ) -> str:
        # json_mode is honoured via the prompt: many compatible endpoints
        # reject a response_format parameter, so it is never sent here.
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }

        url = f"{self._base_url}/chat/completions"
        try:
            response = self._session.post(
                url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.exceptions.ConnectionError as exc:
            raise ProviderConnectionError(
                "Unable to connect to the provider. Please check the API base URL."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise ProviderUnavailableError(
                "The AI provider timed out. Try again later or select another provider."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderError(
                "Could not reach the provider. Check the base URL and your connection."
            ) from exc

        status = response.status_code
        if status in (401, 403):
            raise ProviderAuthError("Authentication failed. Please check your API key.")
        if status == 404:
            if "model" in response.text.lower():
                raise ProviderModelError(
                    "The selected model could not be used. Please check the model name."
                )
            raise ProviderConnectionError(
                "Unable to connect to the provider. Please check the API base URL."
            )
        if status == 400:
            if "model" in response.text.lower():
                raise ProviderModelError(
                    "The selected model could not be used. Please check the model name."
                )
            raise ProviderError(
                "The provider rejected the request. Check the provider configuration."
            )
        if status >= 500:
            raise ProviderUnavailableError(
                "The AI provider is currently unavailable. "
                "Try again later or select another provider."
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "The AI provider returned an unexpected response. Please try again."
            ) from exc
        if content is None or not str(content).strip():
            raise ProviderError(
                "The AI provider returned an empty response. Please try again."
            )
        return str(content)
