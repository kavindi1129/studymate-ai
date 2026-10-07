"""Provider configuration, selection, and instantiation.

Gemini is a built-in provider whose API key stays in .env. Custom
OpenAI-compatible providers (including their API keys) are stored in
providers.json at the project root — that file must stay gitignored. Plain
local storage is a documented limitation of this student project, not
production-grade secret management.
"""

import json
import os
import uuid
from dataclasses import dataclass

from config import settings
from providers.base import AIProvider, ProviderAuthError, ProviderConnectionError, ProviderError, ProviderModelError
from providers.gemini_provider import GeminiProvider
from providers.openai_compatible_provider import OpenAICompatibleProvider

TYPE_GEMINI = "gemini"
TYPE_OPENAI_COMPATIBLE = "openai_compatible"


@dataclass
class ProviderConfig:
    """One configured AI provider."""

    id: str
    name: str
    type: str
    model: str
    base_url: str = ""
    api_key: str = ""

    def masked_api_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) > 4:
            return "••••" + self.api_key[-4:]
        return "••••"


class ProviderManager:
    """Lists, stores, selects, and builds AI providers."""

    def __init__(self, path=None):
        self._path = path or settings.PROVIDERS_FILE
        self._load_error: str | None = None

    # -- persistence ------------------------------------------------------

    def _load(self) -> dict:
        self._load_error = None
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._load_error = (
                "providers.json could not be read, so custom providers were "
                "skipped. Fix or delete the file to restore provider settings."
            )
            return {}
        if not isinstance(data, dict):
            self._load_error = (
                "providers.json has an unexpected format, so custom providers "
                "were skipped."
            )
            return {}
        return data

    def _save(self, data: dict) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, self._path)

    @property
    def load_error(self) -> str | None:
        """Human-readable problem found by the last config load, if any."""
        return self._load_error

    # -- configuration access ----------------------------------------------

    def list_configs(self) -> list[ProviderConfig]:
        """All usable provider configs: built-in Gemini first, then customs."""
        data = self._load()
        gemini_model = str(data.get("gemini_model") or settings.GEMINI_DEFAULT_MODEL).strip()
        configs = [
            ProviderConfig(
                id=TYPE_GEMINI,
                name="Gemini",
                type=TYPE_GEMINI,
                model=gemini_model or settings.GEMINI_DEFAULT_MODEL,
            )
        ]
        for raw in data.get("custom_providers") or []:
            if not isinstance(raw, dict):
                continue
            configs.append(
                ProviderConfig(
                    id=str(raw.get("id") or uuid.uuid4().hex[:8]),
                    name=str(raw.get("name") or "Unnamed provider"),
                    type=TYPE_OPENAI_COMPATIBLE,
                    model=str(raw.get("model") or ""),
                    base_url=str(raw.get("base_url") or ""),
                    api_key=str(raw.get("api_key") or ""),
                )
            )
        return configs

    def get_config(self, provider_id: str) -> ProviderConfig | None:
        for config in self.list_configs():
            if config.id == provider_id:
                return config
        return None

    def active_config(self) -> ProviderConfig | None:
        configs = self.list_configs()
        if not configs:
            return None
        active_id = self._load().get("active_provider_id")
        for config in configs:
            if config.id == active_id:
                return config
        return configs[0]  # default to Gemini

    def set_active(self, provider_id: str) -> bool:
        configs = self.list_configs()
        if not any(config.id == provider_id for config in configs):
            return False
        data = self._load()
        data["active_provider_id"] = provider_id
        self._save(data)
        return True

    def add_custom(
        self, name: str, base_url: str, api_key: str, model: str
    ) -> ProviderConfig:
        """Store a new OpenAI-compatible provider and make it active."""
        data = self._load()
        customs = [
            item
            for item in (data.get("custom_providers") or [])
            if isinstance(item, dict)
        ]
        config = ProviderConfig(
            id=uuid.uuid4().hex[:8],
            name=name,
            type=TYPE_OPENAI_COMPATIBLE,
            model=model,
            base_url=base_url,
            api_key=api_key,
        )
        customs.append(
            {
                "id": config.id,
                "name": config.name,
                "type": config.type,
                "model": config.model,
                "base_url": config.base_url,
                "api_key": config.api_key,
            }
        )
        data["custom_providers"] = customs
        data["active_provider_id"] = config.id
        self._save(data)
        return config

    def remove(self, provider_id: str) -> None:
        if provider_id == TYPE_GEMINI:
            return  # the built-in Gemini provider cannot be removed
        data = self._load()
        customs = [
            item
            for item in (data.get("custom_providers") or [])
            if isinstance(item, dict) and item.get("id") != provider_id
        ]
        data["custom_providers"] = customs
        if data.get("active_provider_id") == provider_id:
            data["active_provider_id"] = TYPE_GEMINI
        self._save(data)

    def set_gemini_model(self, model: str) -> None:
        data = self._load()
        data["gemini_model"] = model
        self._save(data)

    # -- factory ------------------------------------------------------------

    def create_provider(self, config: ProviderConfig) -> AIProvider:
        """Build a provider instance from a stored configuration."""
        if config.type == TYPE_GEMINI:
            api_key = settings.get_gemini_api_key()
            if not api_key:
                raise ProviderAuthError(
                    "Gemini is not configured. Add GEMINI_API_KEY to your "
                    ".env file, or select another provider in Settings."
                )
            if not config.model:
                raise ProviderModelError(
                    "No Gemini model is configured. Set the model in Settings."
                )
            return GeminiProvider(config.name, config.model, api_key)
        if config.type == TYPE_OPENAI_COMPATIBLE:
            if not config.base_url.strip():
                raise ProviderConnectionError(
                    "This provider has no API base URL configured."
                )
            if not config.model.strip():
                raise ProviderModelError(
                    "This provider has no model name configured."
                )
            return OpenAICompatibleProvider(
                config.name,
                config.model.strip(),
                config.base_url.strip(),
                config.api_key.strip(),
            )
        raise ProviderError(f"Unknown provider type: {config.type}")

    def get_active_provider(self) -> AIProvider:
        config = self.active_config()
        if config is None:
            raise ProviderError(
                "No AI provider is configured. Open ⚙️ Settings to add one."
            )
        return self.create_provider(config)
