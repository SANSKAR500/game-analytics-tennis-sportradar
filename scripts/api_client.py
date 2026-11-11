"""Small, reusable HTTP client for the Sportradar Tennis API v3."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import Settings

LOGGER = logging.getLogger(__name__)


class SportradarAPIError(RuntimeError):
    """Raised when the Sportradar API request cannot be completed."""


class SportradarClient:
    """HTTP client with authentication, timeouts, and retry/backoff handling."""

    BASE_URL = "https://api.sportradar.com/tennis"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {"accept": "application/json", "x-api-key": settings.api_key}
        )

    def get(self, feed: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET a Tennis API v3 feed and return decoded JSON."""
        url = (
            f"{self.BASE_URL}/{self.settings.access_level}/v3/"
            f"{self.settings.language}/{feed}.json"
        )
        params = params or {}

        for attempt in range(self.settings.max_retries + 1):
            try:
                response = self.session.get(
                    url, params=params, timeout=self.settings.timeout_seconds
                )

                if response.status_code == 429:
                    if attempt >= self.settings.max_retries:
                        raise SportradarAPIError("Rate limit persisted after retries.")
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    LOGGER.warning("HTTP 429; sleeping %.1fs before retry", delay)
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise SportradarAPIError("API returned a non-object JSON response.")
                return payload

            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status >= 500 and attempt < self.settings.max_retries:
                    delay = 2**attempt
                    LOGGER.warning("HTTP %s; retrying in %ss", status, delay)
                    time.sleep(delay)
                    continue
                raise SportradarAPIError(f"HTTP error {status} for {url}") from exc
            except requests.RequestException as exc:
                if attempt < self.settings.max_retries:
                    delay = 2**attempt
                    LOGGER.warning("Request failed; retrying in %ss: %s", delay, exc)
                    time.sleep(delay)
                    continue
                raise SportradarAPIError(f"Request failed for {url}: {exc}") from exc
            except ValueError as exc:
                raise SportradarAPIError("API returned invalid JSON.") from exc

        raise SportradarAPIError("Request failed unexpectedly.")
