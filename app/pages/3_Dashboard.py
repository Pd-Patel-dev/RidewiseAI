import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from src.analytics.charts import (
    avg_profit_per_mile_chart,
    expense_breakdown_chart,
    expense_by_trip_type_chart,
    miles_comparison_chart,
    profit_by_city_chart,
    profit_by_trip_type_chart,
    revenue_vs_expense_chart,
)
from src.analytics.dashboard_ui import show_kpi_overview
from src.analytics.kpis import calculate_summary_kpis
from src.database.db import init_db
from src.database.ride_repository import get_all_rides

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
init_db()

NO_DATA_MESSAGE = (
    "No rides saved yet. Go to Fare Calculator and save your first ride."
)

st.title("Profit Dashboard")
st.caption("Full business overview built from your saved rides.")

rides_df = get_all_rides()

if rides_df.empty:
    st.info(NO_DATA_MESSAGE)
else:
    kpis = calculate_summary_kpis(rides_df)

    show_kpi_overview(kpis)

    st.divider()
    st.subheader("Charts")

    row1 = st.columns(3)
    row1[0].altair_chart(expense_breakdown_chart(kpis), use_container_width=True)
    row1[1].altair_chart(revenue_vs_expense_chart(kpis), use_container_width=True)
    row1[2].altair_chart(miles_comparison_chart(kpis), use_container_width=True)

    row2 = st.columns(3)
    row2[0].altair_chart(profit_by_trip_type_chart(rides_df), use_container_width=True)
    row2[1].altair_chart(profit_by_city_chart(rides_df), use_container_width=True)
    row2[2].altair_chart(expense_by_trip_type_chart(rides_df), use_container_width=True)

    row3 = st.columns([1, 2, 1])
    with row3[1]:
        st.altair_chart(avg_profit_per_mile_chart(rides_df), use_container_width=True)

    st.caption(
        "Profit charts use rides where a fare was entered. "
        "Rides without fare charged may show $0 profit."
    )

    st.divider()
    st.subheader("All ride data")
    st.dataframe(rides_df, use_container_width=True, hide_index=True)
