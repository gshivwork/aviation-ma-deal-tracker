"""Aviation M&A & Strategic Partnership Deal Tracker.

Streamlit dashboard for exploring aviation industry M&A, codeshares, equity
investments, and strategic partnerships through a build-vs-buy-vs-partner lens.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "deals.db"

# Streamlit Cloud runs this file without the repo root on sys.path, so the
# `etl` package (which lives at the repo root, not under dashboard/) isn't
# importable by default. Add it explicitly before importing from etl.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from etl.load import run as run_etl  # noqa: E402

st.set_page_config(
    page_title="Aviation M&A Deal Tracker",
    page_icon="✈️",
    layout="wide",
)


@st.cache_data
def load_deals(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM deals", conn)
    conn.close()
    df["announced_date"] = pd.to_datetime(df["announced_date"])
    return df


if not DB_PATH.exists():
    # First run on a fresh clone or a fresh Streamlit Cloud deploy: the SQLite
    # file is gitignored (it's derived data), so build it from the seed CSV.
    run_etl()

df = load_deals(str(DB_PATH))

st.title("✈️ Aviation M&A & Strategic Partnership Deal Tracker")
st.caption(
    "Tracking acquisitions, joint ventures, codeshares, equity stakes, and tech "
    "partnerships across the airline industry, framed around build-vs-buy-vs-partner "
    "decisions a Corporate Development team would face."
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

year_min, year_max = int(df["announced_year"].min()), int(df["announced_year"].max())
year_range = st.sidebar.slider(
    "Announced year", min_value=year_min, max_value=year_max, value=(year_min, year_max)
)

deal_types = st.sidebar.multiselect(
    "Deal type", sorted(df["deal_type"].unique()), default=sorted(df["deal_type"].unique())
)
regions = st.sidebar.multiselect(
    "Region", sorted(df["region"].unique()), default=sorted(df["region"].unique())
)
capability_areas = st.sidebar.multiselect(
    "Capability area",
    sorted(df["capability_area"].unique()),
    default=sorted(df["capability_area"].unique()),
)
bbp = st.sidebar.multiselect(
    "Build / Buy / Partner",
    sorted(df["build_buy_partner"].unique()),
    default=sorted(df["build_buy_partner"].unique()),
)

all_companies = sorted(set(df["acquirer"]) | set(df["target_or_partner"]))
selected_companies = st.sidebar.multiselect(
    "Company name",
    all_companies,
    default=[],
    help="Matches a deal if the company appears as either the acquirer or the target/partner. Leave empty to include all.",
)

mask = (
    df["announced_year"].between(year_range[0], year_range[1])
    & df["deal_type"].isin(deal_types)
    & df["region"].isin(regions)
    & df["capability_area"].isin(capability_areas)
    & df["build_buy_partner"].isin(bbp)
)
if selected_companies:
    mask &= df["acquirer"].isin(selected_companies) | df["target_or_partner"].isin(selected_companies)
filtered = df[mask].sort_values("announced_date", ascending=False)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
disclosed = filtered[filtered["deal_value_disclosed"] == 1]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Deals tracked", len(filtered))
col2.metric("Disclosed deal value", f"${disclosed['deal_value_usd_m'].sum():,.0f}M")
col3.metric(
    "Most active capability area",
    filtered["capability_area"].value_counts().idxmax() if len(filtered) else "—",
)
col4.metric(
    "Partner-led share",
    f"{(filtered['build_buy_partner'].eq('Partner').mean() * 100):.0f}%" if len(filtered) else "—",
)

st.divider()

# ---------------------------------------------------------------------------
# Pattern charts
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Deal activity by capability area")
    cap_counts = (
        filtered.groupby("capability_area").size().reset_index(name="deal_count")
        .sort_values("deal_count", ascending=True)
    )
    fig = px.bar(cap_counts, x="deal_count", y="capability_area", orientation="h")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=420)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Build vs. buy vs. partner mix by capability area")
    bbp_mix = (
        filtered.groupby(["capability_area", "build_buy_partner"]).size()
        .reset_index(name="count")
    )
    fig = px.bar(
        bbp_mix, x="count", y="capability_area", color="build_buy_partner",
        orientation="h", barmode="stack",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=420)
    st.plotly_chart(fig, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("Deal volume over time by type")
    timeline = (
        filtered.groupby(["announced_year", "deal_type"]).size().reset_index(name="count")
    )
    fig = px.bar(timeline, x="announced_year", y="count", color="deal_type")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=380)
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader("Disclosed deal value by region")
    region_value = (
        disclosed.groupby("region")["deal_value_usd_m"].sum().reset_index()
        .sort_values("deal_value_usd_m", ascending=True)
    )
    fig = px.bar(region_value, x="deal_value_usd_m", y="region", orientation="h")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=380)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Build vs. buy vs. partner narrative
# ---------------------------------------------------------------------------
st.subheader("Build vs. Buy vs. Partner: capability area read-out")
st.markdown(
    "For each capability area, the dominant strategic posture observed across "
    "tracked deals — useful as a quick reference for where the industry is "
    "converging on a partner-led model versus building or acquiring capability."
)
posture = (
    filtered.groupby("capability_area")["build_buy_partner"]
    .agg(lambda s: s.value_counts().idxmax())
    .reset_index(name="dominant_posture")
)
counts_by_cap = filtered.groupby("capability_area").size().reset_index(name="deal_count")
posture = posture.merge(counts_by_cap, on="capability_area").sort_values(
    "deal_count", ascending=False
)
st.dataframe(posture, use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Deal table
# ---------------------------------------------------------------------------
st.subheader(f"Deal log ({len(filtered)} deals)")
display_cols = [
    "announced_date", "deal_name", "acquirer", "target_or_partner", "deal_type",
    "capability_area", "region", "deal_value_usd_m", "build_buy_partner", "status",
]
st.dataframe(
    filtered[display_cols].rename(columns={"deal_value_usd_m": "deal_value_usd_m_disclosed"}),
    use_container_width=True,
    hide_index=True,
)

with st.expander("Strategic rationale & sources for selected deal"):
    selected_name = st.selectbox("Select a deal", filtered["deal_name"].tolist())
    detail = filtered[filtered["deal_name"] == selected_name].iloc[0]
    st.markdown(f"**Rationale:** {detail['strategic_rationale']}")
    st.markdown(f"**Source:** [{detail['source_name']}]({detail['source_url']})")
    st.markdown(f"**Status:** {detail['status']}")
