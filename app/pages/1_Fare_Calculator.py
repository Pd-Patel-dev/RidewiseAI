import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from config.settings import AIRPORT_FEE
from src.database.db import init_db
from src.database.ride_repository import save_ride
from src.pricing.profit import (
    calculate_actual_profit,
    calculate_profit_per_customer_mile,
    calculate_profit_per_expense_mile,
)
from src.pricing.rule_based import TRIP_TYPES, calculate_rule_based_fare

st.set_page_config(page_title="Fare Calculator", page_icon="💰", layout="wide")
init_db()

st.title("Fare Calculator")
st.caption(
    "Enter trip details below. Expenses are based on how many miles your car "
    "actually drives, not driver time."
)
st.info(
    "Because you are the driver, driver time is not counted as an expense. "
    "Fuel and maintenance use **expense miles** — the miles your car actually drives."
)


def validate_inputs(one_way_miles, mpg, gas_price, city):
    errors = []
    if one_way_miles <= 0:
        errors.append("One-way miles must be greater than 0.")
    if mpg <= 0:
        errors.append("Vehicle MPG must be greater than 0.")
    if gas_price <= 0:
        errors.append("Gas price must be greater than 0.")
    if not city.strip():
        errors.append("City cannot be empty.")
    return errors


def build_ride_data(ride, result):
    """Build the dictionary that gets saved to SQLite."""
    return {
        "trip_type": result["trip_type"],
        "one_way_miles": result["one_way_miles"],
        "customer_miles": result["customer_miles"],
        "expense_miles": result["expense_miles"],
        "mpg": ride["mpg"],
        "gas_price": ride["gas_price"],
        "trip_minutes": ride["trip_minutes"],
        "waiting_minutes": ride["waiting_minutes"],
        "city": ride["city"],
        "is_airport": ride["is_airport"],
        "tolls": ride["tolls"],
        "airport_fee": ride["airport_fee"],
        "fare_charged": ride["fare_charged"],
        "fuel_cost": result["fuel_cost"],
        "maintenance_cost": result["maintenance_cost"],
        "total_expense": result["total_expense"],
        "recommended_fare": result["recommended_fare"],
        "actual_profit": ride["actual_profit"],
        "profit_per_expense_mile": ride["profit_per_expense_mile"],
        "profit_per_customer_mile": ride["profit_per_customer_mile"],
    }


with st.form("fare_calculator_form"):
    st.markdown("#### Trip details")
    trip_left, trip_right = st.columns(2)

    with trip_left:
        trip_type = st.selectbox("Trip type", TRIP_TYPES)
        one_way_miles = st.number_input(
            "One-way miles", min_value=0.0, value=10.0, step=0.1
        )
        trip_minutes = st.number_input(
            "Trip minutes (optional)", min_value=0.0, value=30.0, step=1.0
        )
        waiting_minutes = st.number_input(
            "Waiting minutes (optional)", min_value=0.0, value=0.0, step=1.0
        )

    with trip_right:
        city = st.text_input("City", placeholder="e.g. Chicago")
        is_airport = st.toggle("Airport trip", value=False)
        if is_airport:
            st.caption(f"Airport fee: ${AIRPORT_FEE:.2f} will be added to total expense.")

    st.divider()
    st.markdown("#### Vehicle & trip fees")
    vehicle_left, vehicle_right = st.columns(2)

    with vehicle_left:
        mpg = st.number_input("Vehicle MPG", min_value=0.0, value=25.0, step=0.1)
        gas_price = st.number_input(
            "Gas price per gallon ($)", min_value=0.0, value=3.50, step=0.01
        )

    with vehicle_right:
        tolls = st.number_input("Tolls ($)", min_value=0.0, value=0.0, step=0.5)
        profit_margin_pct = st.slider("Profit margin (%)", 0, 100, 30)

    st.divider()
    st.markdown("#### Customer fare")
    fare_charged = st.number_input(
        "Fare charged by customer ($)", min_value=0.0, value=0.0, step=0.50
    )

    st.divider()
    _, btn_col, _ = st.columns([2, 1, 2])
    with btn_col:
        calculate_clicked = st.form_submit_button(
            "Calculate Fare", type="primary", use_container_width=True
        )

if calculate_clicked:
    errors = validate_inputs(one_way_miles, mpg, gas_price, city)

    if errors:
        for message in errors:
            st.error(message)
        st.session_state.pop("last_ride", None)
    else:
        airport_fee = AIRPORT_FEE if is_airport else 0.0
        profit_margin = profit_margin_pct / 100

        result = calculate_rule_based_fare(
            trip_type=trip_type,
            one_way_miles=one_way_miles,
            mpg=mpg,
            gas_price=gas_price,
            tolls=tolls,
            airport_fee=airport_fee,
            profit_margin=profit_margin,
            trip_minutes=trip_minutes,
            waiting_minutes=waiting_minutes,
        )

        actual_profit = None
        profit_per_expense_mile = None
        profit_per_customer_mile = None
        if fare_charged > 0:
            actual_profit = calculate_actual_profit(fare_charged, result["total_expense"])
            profit_per_expense_mile = calculate_profit_per_expense_mile(
                actual_profit, result["expense_miles"]
            )
            profit_per_customer_mile = calculate_profit_per_customer_mile(
                actual_profit, result["customer_miles"]
            )

        st.session_state["last_ride"] = {
            "mpg": mpg,
            "gas_price": gas_price,
            "trip_minutes": trip_minutes,
            "waiting_minutes": waiting_minutes,
            "city": city.strip(),
            "is_airport": is_airport,
            "tolls": tolls,
            "airport_fee": airport_fee,
            "fare_charged": fare_charged,
            "actual_profit": actual_profit,
            "profit_per_expense_mile": profit_per_expense_mile,
            "profit_per_customer_mile": profit_per_customer_mile,
            "result": result,
        }

if "last_ride" in st.session_state:
    ride = st.session_state["last_ride"]
    result = ride["result"]

    st.divider()
    st.subheader("Results")
    st.caption(
        f"**{ride['city']}** · **{result['trip_type']}**"
        + (" · Airport trip" if ride["is_airport"] else "")
        + f" · {result['one_way_miles']:.1f} mi one-way"
    )

    st.markdown("**Mile breakdown**")
    mile_cols = st.columns(2)
    mile_cols[0].metric("Customer Miles", f"{result['customer_miles']:.1f}")
    mile_cols[1].metric("Expense Miles", f"{result['expense_miles']:.1f}")

    st.markdown("**Expense breakdown**")
    expense_cols = st.columns(5)
    expense_cols[0].metric("Fuel Cost", f"${result['fuel_cost']:.2f}")
    expense_cols[1].metric("Maintenance Cost", f"${result['maintenance_cost']:.2f}")
    expense_cols[2].metric("Tolls", f"${ride['tolls']:.2f}")
    expense_cols[3].metric("Airport Fee", f"${ride['airport_fee']:.2f}")
    expense_cols[4].metric("Total Expense", f"${result['total_expense']:.2f}")

    st.markdown("**Fare & profit**")
    fare_cols = st.columns(5)
    fare_cols[0].metric("Recommended Fare", f"${result['recommended_fare']:.2f}")
    fare_cols[1].metric("Fare Charged", f"${ride['fare_charged']:.2f}")

    if ride["actual_profit"] is not None:
        fare_cols[2].metric("Actual Profit", f"${ride['actual_profit']:.2f}")
        fare_cols[3].metric("Profit / Expense Mile", f"${ride['profit_per_expense_mile']:.2f}")
        fare_cols[4].metric("Profit / Customer Mile", f"${ride['profit_per_customer_mile']:.2f}")
    else:
        fare_cols[2].metric("Actual Profit", "—")
        fare_cols[3].metric("Profit / Expense Mile", "—")
        fare_cols[4].metric("Profit / Customer Mile", "—")

    st.divider()
    _, save_col, _ = st.columns([2, 1, 2])
    with save_col:
        if st.button("Save Ride", type="primary", use_container_width=True):
            ride_data = build_ride_data(ride, result)
            saved = save_ride(ride_data)
            st.success(f"Ride saved to database (ID: {saved.id}).")
