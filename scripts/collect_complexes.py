"""Collect complexes and nested venues from Sportradar."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from api_client import SportradarClient
from config import data_path, get_settings

LOGGER = logging.getLogger(__name__)


def _require_key(payload: dict, key: str) -> None:
    """Raise if the API response does not have the expected root key.

    Without this check a changed response shape would silently produce empty CSVs.
    """
    if key not in payload:
        raise ValueError(
            f"Unexpected API response: root key '{key}' missing. "
            f"Keys received: {sorted(payload.keys())}"
        )
COMPLEX_COLUMNS = ["complex_id", "complex_name"]
VENUE_COLUMNS = [
    "venue_id", "venue_name", "city_name", "country_name", "country_code",
    "timezone", "complex_id"
]


def collect(client: SportradarClient) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flatten complex/venue nesting into relational tables."""
    payload = client.get("complexes")
    _require_key(payload, "complexes")
    complexes: list[dict[str, str]] = []
    venues: list[dict[str, str]] = []

    for complex_item in payload.get("complexes", []):
        complex_id = complex_item.get("id")
        complex_name = complex_item.get("name")
        if not complex_id or not complex_name:
            LOGGER.warning("Skipping complex missing id/name: %s", complex_item)
            continue
        complexes.append({"complex_id": complex_id, "complex_name": complex_name})

        for venue in complex_item.get("venues", []):
            required = [venue.get("id"), venue.get("name"), venue.get("country_code")]
            if not all(required):
                LOGGER.warning("Skipping incomplete venue %s", venue)
                continue
            venues.append(
                {
                    "venue_id": venue["id"],
                    "venue_name": venue["name"],
                    "city_name": venue.get("city_name") or "Unknown",
                    "country_name": venue.get("country_name") or "Unknown",
                    "country_code": venue["country_code"],
                    "timezone": venue.get("timezone") or "Unknown",
                    "complex_id": complex_id,
                }
            )

    complex_df = pd.DataFrame(complexes, columns=COMPLEX_COLUMNS).drop_duplicates(
        subset=["complex_id"]
    )
    venue_df = pd.DataFrame(venues, columns=VENUE_COLUMNS).drop_duplicates(
        subset=["venue_id"]
    )
    return complex_df, venue_df


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    complexes, venues = collect(SportradarClient(get_settings()))
    if args.dry_run:
        print(f"complexes={len(complexes)} venues={len(venues)}")
        return
    complexes.to_csv(data_path("complexes.csv"), index=False)
    venues.to_csv(data_path("venues.csv"), index=False)
    print(f"Wrote {len(complexes)} complexes and {len(venues)} venues.")


if __name__ == "__main__":
    main()
