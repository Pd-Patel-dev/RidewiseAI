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

st.title("Ride History")
st.caption("All rides saved from the Fare Calculator.")

rides_df = get_all_rides()

if rides_df.empty:
    st.info("No rides saved yet. Go to Fare Calculator, calculate a fare, and click Save Ride.")
else:
    total_rides = len(rides_df)
    total_revenue = rides_df["fare_charged"].sum()
    total_expense = rides_df["total_expense"].sum()
    total_profit = rides_df["actual_profit"].fillna(0).sum()
    total_expense_miles = rides_df["expense_miles"].sum()

    profit_per_expense_values = rides_df["profit_per_expense_mile"].dropna()
    avg_profit_per_expense_mile = (
        profit_per_expense_values.mean() if not profit_per_expense_values.empty else 0.0
    )

    row1 = st.columns(3)
    row1[0].metric("Total Rides", total_rides)
    row1[1].metric("Total Revenue", f"${total_revenue:,.2f}")
    row1[2].metric("Total Expense", f"${total_expense:,.2f}")

    row2 = st.columns(3)
    row2[0].metric("Total Profit", f"${total_profit:,.2f}")
    row2[1].metric("Total Expense Miles", f"{total_expense_miles:,.1f}")
    row2[2].metric("Avg Profit / Expense Mile", f"${avg_profit_per_expense_mile:,.2f}")

    st.divider()
    st.subheader("Saved Rides")

    display_columns = [
        "created_at",
        "trip_type",
        "city",
        "one_way_miles",
        "customer_miles",
        "expense_miles",
        "fare_charged",
        "total_expense",
        "actual_profit",
        "profit_per_expense_mile",
        "profit_per_customer_mile",
    ]
    st.dataframe(
        rides_df[display_columns],
        use_container_width=True,
        hide_index=True,
    )
