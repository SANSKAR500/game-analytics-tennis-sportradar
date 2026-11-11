"""Collect doubles competitor rankings and competitor reference data."""

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
COMPETITOR_COLUMNS = ["competitor_id", "name", "country", "country_code", "abbreviation"]
RANKING_COLUMNS = ["rank", "movement", "points", "competitions_played", "competitor_id"]


def collect(client: SportradarClient) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Flatten all ranking groups into competitors and ranking rows.

    The source contains ranking-level year/week metadata. The current schema
    intentionally does not persist those fields; they are returned as metadata
    so the caller can log the snapshot without changing the schema.
    """
    payload = client.get("double_competitors_rankings")
    _require_key(payload, "rankings")
    competitors: dict[str, dict[str, str]] = {}
    rankings: list[dict[str, int | str]] = []
    snapshots: list[dict] = []

    for ranking in payload.get("rankings", []):
        snapshots.append(
            {
                "name": ranking.get("name"),
                "gender": ranking.get("gender"),
                "type_id": ranking.get("type_id"),
                "year": ranking.get("year"),
                "week": ranking.get("week"),
            }
        )
        for row in ranking.get("competitor_rankings", []):
            competitor = row.get("competitor") or {}
            required = [
                competitor.get("id"), competitor.get("name"),
                competitor.get("country_code"), row.get("rank"), row.get("points")
            ]
            if any(value is None for value in required):
                LOGGER.warning("Skipping incomplete ranking row: %s", row)
                continue
            competitor_id = str(competitor["id"])
            competitors[competitor_id] = {
                "competitor_id": competitor_id,
                "name": str(competitor["name"]),
                "country": str(competitor.get("country") or "Unknown"),
                "country_code": str(competitor["country_code"]),
                "abbreviation": str(competitor.get("abbreviation") or ""),
            }
            rankings.append(
                {
                    "rank": int(row["rank"]),
                    "movement": int(row.get("movement") or 0),
                    "points": int(row["points"]),
                    "competitions_played": int(row.get("competitions_played") or 0),
                    "competitor_id": competitor_id,
                }
            )

    competitor_df = pd.DataFrame(list(competitors.values()), columns=COMPETITOR_COLUMNS)
    ranking_df = pd.DataFrame(rankings, columns=RANKING_COLUMNS)
    return competitor_df, ranking_df, snapshots


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    competitors, rankings, snapshots = collect(SportradarClient(get_settings()))
    if args.dry_run:
        print(f"competitors={len(competitors)} rankings={len(rankings)}")
        print(f"snapshots={snapshots}")
        return
    competitors.to_csv(data_path("competitors.csv"), index=False)
    rankings.to_csv(data_path("competitor_rankings.csv"), index=False)
    print(f"Wrote {len(competitors)} competitors and {len(rankings)} ranking rows.")
    print(f"Snapshot metadata: {snapshots}")


if __name__ == "__main__":
    main()
