"""Configuration helpers for the Sportradar collection scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    api_key: str
    access_level: str = "trial"
    language: str = "en"
    timeout_seconds: float = 30.0
    max_retries: int = 4


def get_settings() -> Settings:
    """Return validated application settings."""
    api_key = os.getenv("SPORTRADAR_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "SPORTRADAR_API_KEY is missing. Put it in .env or export it."
        )
    return Settings(
        api_key=api_key,
        access_level=os.getenv("SPORTRADAR_ACCESS_LEVEL", "trial"),
        language=os.getenv("SPORTRADAR_LANGUAGE", "en"),
        timeout_seconds=float(os.getenv("SPORTRADAR_TIMEOUT", "30")),
        max_retries=int(os.getenv("SPORTRADAR_MAX_RETRIES", "4")),
    )


def data_path(filename: str) -> Path:
    """Return an absolute path under the project's data directory."""
    path = PROJECT_ROOT / "data" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
