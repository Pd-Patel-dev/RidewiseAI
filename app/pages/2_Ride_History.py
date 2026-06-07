import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from src.database.db import init_db
from src.database.ride_repository import get_all_rides

st.set_page_config(page_title="Ride History", page_icon="📋", layout="wide")
init_db()

NO_DATA_MESSAGE = (
    "No rides saved yet. Go to Fare Calculator and save your first ride."
)


st.title("Ride History")
st.caption("Browse saved rides and filter by trip type, city, or airport trips.")

rides_df = get_all_rides()

if rides_df.empty:
    st.info(NO_DATA_MESSAGE)
else:
    st.markdown("#### Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    trip_types = ["All"] + sorted(rides_df["trip_type"].unique().tolist())
    cities = ["All"] + sorted(rides_df["city"].unique().tolist())
    airport_options = ["All", "Yes", "No"]

    with filter_col1:
        selected_trip_type = st.selectbox("Trip type", trip_types)
    with filter_col2:
        selected_city = st.selectbox("City", cities)
    with filter_col3:
        selected_airport = st.selectbox("Airport trip", airport_options)

    filtered_df = rides_df.copy()

    if selected_trip_type != "All":
        filtered_df = filtered_df[filtered_df["trip_type"] == selected_trip_type]
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["city"] == selected_city]
    if selected_airport == "Yes":
        filtered_df = filtered_df[filtered_df["is_airport"]]
    elif selected_airport == "No":
        filtered_df = filtered_df[~filtered_df["is_airport"]]

    if filtered_df.empty:
        st.warning("No rides match your filters. Try changing the filter options.")
    else:
        st.subheader("Saved Rides")

        display_columns = [
            "created_at",
            "trip_type",
            "city",
            "is_airport",
            "one_way_miles",
            "customer_miles",
            "expense_miles",
            "fuel_cost",
            "maintenance_cost",
            "tolls",
            "airport_fee",
            "total_expense",
            "recommended_fare",
            "fare_charged",
            "actual_profit",
            "profit_per_expense_mile",
            "profit_per_customer_mile",
        ]
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )
