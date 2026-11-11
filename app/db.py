"""Database connection and parameterized, read-only query helpers.

Settings are read from Streamlit secrets when running on Streamlit Community Cloud,
and from environment variables (or a local .env file) otherwise.
"""

from __future__ import annotations

import os
from decimal import Decimal
from contextlib import contextmanager
from typing import Iterator

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()


def _setting(name: str, default: str = "") -> str:
    """Return a setting from st.secrets if available, else from the environment."""
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001 - no secrets file locally is fine
        pass
    return os.getenv(name, default)


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield a read-only PostgreSQL connection."""
    conn = psycopg.connect(
        host=_setting("DB_HOST", "localhost"),
        port=_setting("DB_PORT", "5432"),
        dbname=_setting("DB_NAME", "tennis_db"),
        user=_setting("DB_USER", "postgres"),
        password=_setting("DB_PASSWORD", ""),
        sslmode=_setting("DB_SSLMODE", "prefer"),
    )
    conn.read_only = True
    try:
        yield conn
    finally:
        conn.close()


def read_query(sql: str, params: tuple | dict | None = None) -> pd.DataFrame:
    """Execute a parameterized SELECT and return a DataFrame."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [col.name for col in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
    # PostgreSQL NUMERIC values arrive as Decimal; convert so charts and math work.
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df
