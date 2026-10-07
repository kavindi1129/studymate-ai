"""Application-level configuration and environment access."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "StudyMate AI"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "providers.json"

MAX_INPUT_CHARS = 90_000  # keep study material within the model's context window
# 3.5-flash was verified working on 2026-10-07; 3.8-flash was hanging
# provider-side that day, so it stays available via Settings instead.
GEMINI_DEFAULT_MODEL = "gemini-3.5-flash"


def get_gemini_api_key() -> str:
    """Return the configured Gemini key (GEMINI_API_KEY or GOOGLE_API_KEY)."""
    return os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
