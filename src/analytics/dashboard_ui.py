import streamlit as st


def show_kpi_overview(kpis: dict) -> None:
    """Display KPI metrics in an even 4-column grid."""
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.04);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            min-height: 5.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    total_fees = kpis["total_tolls"] + kpis["total_airport_fees"]
    mile_gap = kpis["total_expense_miles"] - kpis["total_customer_miles"]

    st.markdown("##### Revenue & profit")
    r1 = st.columns(4)
    r1[0].metric("Total Rides", kpis["total_rides"])
    r1[1].metric("Total Revenue", f"${kpis['total_revenue']:,.2f}")
    r1[2].metric("Recommended Fare", f"${kpis['total_recommended_fare']:,.2f}")
    r1[3].metric("Total Profit", f"${kpis['total_profit']:,.2f}")

    r2 = st.columns(4)
    r2[0].metric("Avg Fare Charged", f"${kpis['avg_fare_charged']:,.2f}")
    r2[1].metric("Avg Profit / Ride", f"${kpis['avg_profit_per_ride']:,.2f}")
    r2[2].metric("Profit Margin", f"{kpis['profit_margin_pct']:.1f}%")
    r2[3].metric("Airport Trips", kpis["airport_trips"])

    st.markdown("##### Expense breakdown")
    r3 = st.columns(4)
    r3[0].metric("Total Expense", f"${kpis['total_expense']:,.2f}")
    r3[1].metric("Fuel Cost", f"${kpis['total_fuel_cost']:,.2f}")
    r3[2].metric("Maintenance Cost", f"${kpis['total_maintenance_cost']:,.2f}")
    r3[3].metric("Tolls", f"${kpis['total_tolls']:,.2f}")

    r4 = st.columns(4)
    r4[0].metric("Airport Fees", f"${kpis['total_airport_fees']:,.2f}")
    r4[1].metric("Total Fees", f"${total_fees:,.2f}")
    r4[2].metric("Avg Expense / Ride", f"${kpis['avg_expense_per_ride']:,.2f}")
    r4[3].metric("Cost / Expense Mile", f"${kpis['cost_per_expense_mile']:,.2f}")

    st.markdown("##### Profit efficiency")
    fee_share = (
        (total_fees / kpis["total_expense"]) * 100 if kpis["total_expense"] > 0 else 0.0
    )
    fuel_share = (
        (kpis["total_fuel_cost"] / kpis["total_expense"]) * 100
        if kpis["total_expense"] > 0
        else 0.0
    )
    r5 = st.columns(4)
    r5[0].metric("Avg Profit / Customer Mile", f"${kpis['avg_profit_per_customer_mile']:,.2f}")
    r5[1].metric("Avg Profit / Expense Mile", f"${kpis['avg_profit_per_expense_mile']:,.2f}")
    r5[2].metric("Fees % of Expense", f"{fee_share:.1f}%")
    r5[3].metric("Fuel % of Expense", f"{fuel_share:.1f}%")

    st.markdown("##### Miles")
    r6 = st.columns(4)
    r6[0].metric("One-Way Miles", f"{kpis['total_one_way_miles']:,.1f}")
    r6[1].metric("Customer Miles", f"{kpis['total_customer_miles']:,.1f}")
    r6[2].metric("Expense Miles", f"{kpis['total_expense_miles']:,.1f}")
    r6[3].metric(
        "Mile Gap",
        f"{mile_gap:,.1f}",
        help="Expense miles minus customer miles (empty return driving)",
    )
