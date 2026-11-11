"""Tests for the CSV validation layer."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_data import validate  # noqa: E402


def test_reference_csvs_are_valid() -> None:
    """The supplied corrected reference data should pass validation."""
    errors = validate(Path(__file__).resolve().parents[1] / "data")
    assert errors == []
