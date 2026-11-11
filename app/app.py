"""Streamlit dashboard for Tennis Game Analytics."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))
from db import read_query  # noqa: E402
import queries as q  # noqa: E402

st.set_page_config(page_title="Tennis Game Analytics", page_icon="🎾", layout="wide")

st.title("🎾 Tennis Game Analytics")
st.caption("Sportradar doubles ranking snapshot + competition and venue reference data")

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["Overview", "Competitors", "Countries", "Leaderboards", "Competitions", "Venues"],
    )
    st.divider()
    st.caption("Data scope: current database snapshot. Rankings are doubles only.")


@st.cache_data(ttl=600, show_spinner=False)
def cached_query(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Cache query results for 10 minutes."""
    return read_query(sql, params)


def run(sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
    """Run a read-only parameterized query with friendly error handling."""
    try:
        return cached_query(sql, params)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Database query failed: {exc}")
        st.stop()


if page == "Overview":
    st.subheader("Overview")
    summary = run(q.HOME).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Competitors", int(summary.total_competitors))
    c2.metric("Countries", int(summary.countries_represented))
    c3.metric("Highest points", f"{int(summary.highest_points):,}")

    st.info(
        "The current schema stores the ranking rows without week/year. "
        "Interpret the rankings as the latest loaded snapshot, not a historical series."
    )

elif page == "Competitors":
    st.subheader("Competitor search and filters")
    tab1, tab2, tab3 = st.tabs(["Search", "Filter", "Details"])

    with tab1:
        name = st.text_input("Name contains", placeholder="e.g. Pavic")
        page_size = st.selectbox("Rows per page", [10, 25, 50], index=0)
        page_no = st.number_input("Page", min_value=1, value=1, step=1)
        df = run(q.SEARCH, {"pattern": f"%{name}%", "limit": page_size, "offset": (page_no - 1) * page_size})
        st.dataframe(df, width="stretch", hide_index=True)

    with tab2:
        min_rank, max_rank = st.slider("Rank range", 1, 500, (1, 50))
        countries = run("SELECT DISTINCT country FROM competitors ORDER BY country")["country"].tolist()
        country = st.selectbox("Country", ["All"] + countries)
        min_points = st.number_input("Minimum points", min_value=0, value=0, step=100)
        page_no = st.number_input("Page", min_value=1, value=1, step=1, key="filter_page")
        df = run(
            q.FILTER,
            {
                "min_rank": min_rank, "max_rank": max_rank,
                "country": "" if country == "All" else country,
                "min_points": min_points, "limit": 25,
                "offset": (page_no - 1) * 25,
            },
        )
        st.dataframe(df, width="stretch", hide_index=True)

    with tab3:
        ids = run("SELECT competitor_id, name FROM competitors ORDER BY name")
        selected = st.selectbox("Competitor", ids.itertuples(index=False), format_func=lambda x: x.name)
        detail = run(q.DETAIL, {"competitor_id": selected.competitor_id})
        st.dataframe(detail, width="stretch", hide_index=True)

elif page == "Countries":
    st.subheader("Country analysis")
    df = run(q.COUNTRIES)
    st.dataframe(df, width="stretch", hide_index=True)
    st.bar_chart(df.set_index("country")["avg_points"].head(20))

elif page == "Leaderboards":
    st.subheader("Leaderboards")
    left, right = st.columns(2)
    with left:
        st.markdown("**Top 10 by points**")
        st.dataframe(run(q.TOP_POINTS), width="stretch", hide_index=True)
    with right:
        st.markdown("**Biggest rank movers**")
        st.dataframe(run(q.MOVERS), width="stretch", hide_index=True)

elif page == "Competitions":
    st.subheader("Competition hierarchy")
    types = run("SELECT DISTINCT type FROM competitions ORDER BY type")["type"].tolist()
    categories = run("SELECT DISTINCT category_name FROM categories ORDER BY category_name")["category_name"].tolist()
    c1, c2 = st.columns(2)
    selected_type = c1.selectbox("Competition type", ["All"] + types)
    selected_category = c2.selectbox("Category / level stand-in", ["All"] + categories)
    st.caption("No level column exists in the project schema, so category is used as the dashboard stand-in.")
    page_no = st.number_input("Page", min_value=1, value=1, step=1, key="competition_page")
    df = run(
        q.COMPETITIONS,
        {
            "type": "" if selected_type == "All" else selected_type,
            "category": "" if selected_category == "All" else selected_category,
            "limit": 50, "offset": (page_no - 1) * 50,
        },
    )
    st.dataframe(df, width="stretch", hide_index=True)
    st.caption("Rows with a parent_id belong to a parent competition; the current schema intentionally does not enforce a self-FK on parent_id.")

elif page == "Venues":
    st.subheader("Venues by complex and country")
    countries = run("SELECT DISTINCT country_name FROM venues ORDER BY country_name")["country_name"].tolist()
    complexes = run("SELECT DISTINCT complex_name FROM complexes ORDER BY complex_name")["complex_name"].tolist()
    c1, c2 = st.columns(2)
    country = c1.selectbox("Country", ["All"] + countries)
    complex_name = c2.selectbox("Complex", ["All"] + complexes)
    page_no = st.number_input("Page", min_value=1, value=1, step=1, key="venue_page")
    df = run(
        q.VENUES,
        {
            "country": "" if country == "All" else country,
            "complex": "" if complex_name == "All" else complex_name,
            "limit": 50, "offset": (page_no - 1) * 50,
        },
    )
    st.dataframe(df, width="stretch", hide_index=True)
