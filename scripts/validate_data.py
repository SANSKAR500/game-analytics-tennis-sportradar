"""Validate CSV row counts, uniqueness, required fields, and FK consistency."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import PROJECT_ROOT

REQUIRED = {
    "categories.csv": ["category_id", "category_name"],
    "competitions.csv": ["competition_id", "competition_name", "parent_id", "type", "gender", "category_id"],
    "complexes.csv": ["complex_id", "complex_name"],
    "venues.csv": ["venue_id", "venue_name", "city_name", "country_name", "country_code", "timezone", "complex_id"],
    "competitors.csv": ["competitor_id", "name", "country", "country_code", "abbreviation"],
    "competitor_rankings.csv": ["rank", "movement", "points", "competitions_played", "competitor_id"],
}


def load_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    """Load one CSV and validate its columns."""
    df = pd.read_csv(path, keep_default_na=False)
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    if list(df.columns) != columns:
        raise ValueError(f"{path.name}: expected columns {columns}, found {list(df.columns)}")
    return df


def validate(data_dir: Path) -> list[str]:
    """Return validation errors; an empty list means the dataset is valid."""
    errors: list[str] = []
    dfs = {name: load_csv(data_dir / name, cols) for name, cols in REQUIRED.items()}

    unique_keys = {
        "categories.csv": "category_id",
        "competitions.csv": "competition_id",
        "complexes.csv": "complex_id",
        "venues.csv": "venue_id",
        "competitors.csv": "competitor_id",
    }
    for filename, key in unique_keys.items():
        if dfs[filename][key].duplicated().any():
            errors.append(f"{filename}: duplicate {key} values")

    for filename, df in dfs.items():
        for col in REQUIRED[filename]:
            if df[col].astype(str).str.strip().eq("").any() and col not in {"parent_id"}:
                errors.append(f"{filename}: blank values in required column {col}")

    category_ids = set(dfs["categories.csv"]["category_id"])
    bad_categories = set(dfs["competitions.csv"]["category_id"]) - category_ids
    if bad_categories:
        errors.append(f"competitions.csv: unknown category_id values {sorted(bad_categories)}")

    complex_ids = set(dfs["complexes.csv"]["complex_id"])
    bad_complexes = set(dfs["venues.csv"]["complex_id"]) - complex_ids
    if bad_complexes:
        errors.append(f"venues.csv: unknown complex_id values {sorted(bad_complexes)}")

    competitor_ids = set(dfs["competitors.csv"]["competitor_id"])
    bad_competitors = set(dfs["competitor_rankings.csv"]["competitor_id"]) - competitor_ids
    if bad_competitors:
        errors.append(f"competitor_rankings.csv: unknown competitor_id values {sorted(bad_competitors)}")

    return errors


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data")
    args = parser.parse_args()
    errors = validate(args.data_dir)
    print("CSV validation summary")
    for filename in REQUIRED:
        print(f"  {filename}: {len(pd.read_csv(args.data_dir / filename))} rows")
    if errors:
        print("\nFAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("\nPASSED: schema, required fields, uniqueness, and foreign-key consistency.")


if __name__ == "__main__":
    main()
