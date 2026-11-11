"""Collect competitions and categories from Sportradar."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

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

COMPETITION_COLUMNS = [
    "competition_id",
    "competition_name",
    "parent_id",
    "type",
    "gender",
    "category_id",
]
CATEGORY_COLUMNS = ["category_id", "category_name"]


def collect(client: SportradarClient) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flatten the competitions response into two relational datasets."""
    payload = client.get("competitions")
    _require_key(payload, "competitions")
    rows: list[dict[str, str | None]] = []
    categories: dict[str, str] = {}

    for item in payload.get("competitions", []):
        if not item.get("id") or not item.get("name"):
            LOGGER.warning("Skipping competition missing id/name: %s", item)
            continue
        category = item.get("category") or {}
        category_id = category.get("id")
        category_name = category.get("name")
        if category_id and category_name:
            categories[str(category_id)] = str(category_name)
        rows.append(
            {
                "competition_id": item["id"],
                "competition_name": item["name"],
                "parent_id": item.get("parent_id") or None,
                "type": item.get("type") or "",
                "gender": item.get("gender") or "",
                "category_id": category_id,
            }
        )

    competitions = pd.DataFrame(rows, columns=COMPETITION_COLUMNS).drop_duplicates(
        subset=["competition_id"]
    )
    category_df = pd.DataFrame(
        list(categories.items()), columns=CATEGORY_COLUMNS
    ).drop_duplicates(subset=["category_id"])
    return category_df, competitions


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print counts only.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    categories, competitions = collect(SportradarClient(get_settings()))
    if args.dry_run:
        print(f"categories={len(categories)} competitions={len(competitions)}")
        return
    categories.to_csv(data_path("categories.csv"), index=False)
    competitions.to_csv(data_path("competitions.csv"), index=False)
    print(f"Wrote {len(categories)} categories and {len(competitions)} competitions.")


if __name__ == "__main__":
    main()
