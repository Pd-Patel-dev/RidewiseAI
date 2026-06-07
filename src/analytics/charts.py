import altair as alt
import pandas as pd

CHART_HEIGHT = 220
COLOR_SCALE = alt.Scale(scheme="tealblues")


def _base_chart(chart: alt.Chart) -> alt.Chart:
    """Apply compact styling that fits the Streamlit dark theme."""
    return (
        chart.configure_view(strokeWidth=0, fill="rgba(0,0,0,0)")
        .configure_axis(
            labelAngle=0,
            labelColor="#b0b0b0",
            titleColor="#b0b0b0",
            gridColor="#2a2a2a",
            domainColor="#3a3a3a",
        )
        .configure_title(color="#fafafa", fontSize=14, anchor="start")
    )


def _single_series_bar(data: pd.DataFrame, x_col: str, y_col: str, title: str) -> alt.Chart:
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{x_col}:N", sort="-y", title="", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y_col}:Q", title=""),
            color=alt.Color(f"{x_col}:N", legend=None, scale=COLOR_SCALE),
            tooltip=[x_col, alt.Tooltip(f"{y_col}:Q", format=",.2f")],
        )
        .properties(height=CHART_HEIGHT, title=title)
    )
    return _base_chart(chart)


def expense_breakdown_chart(kpis: dict) -> alt.Chart:
    data = pd.DataFrame(
        {
            "Category": ["Fuel", "Maintenance", "Tolls", "Airport"],
            "Amount": [
                kpis["total_fuel_cost"],
                kpis["total_maintenance_cost"],
                kpis["total_tolls"],
                kpis["total_airport_fees"],
            ],
        }
    )
    return _single_series_bar(data, "Category", "Amount", "Expense breakdown")


def revenue_vs_expense_chart(kpis: dict) -> alt.Chart:
    data = pd.DataFrame(
        {
            "Type": ["Revenue", "Expense"],
            "Amount": [kpis["total_revenue"], kpis["total_expense"]],
        }
    )
    return _single_series_bar(data, "Type", "Amount", "Revenue vs expense")


def miles_comparison_chart(kpis: dict) -> alt.Chart:
    data = pd.DataFrame(
        {
            "Type": ["Customer", "Expense"],
            "Miles": [kpis["total_customer_miles"], kpis["total_expense_miles"]],
        }
    )
    return _single_series_bar(data, "Type", "Miles", "Miles driven")


def profit_by_trip_type_chart(rides_df: pd.DataFrame) -> alt.Chart:
    data = (
        rides_df.groupby("trip_type")["actual_profit"]
        .sum()
        .fillna(0)
        .reset_index(name="Profit")
    )
    return _single_series_bar(data, "trip_type", "Profit", "Profit by trip type")


def profit_by_city_chart(rides_df: pd.DataFrame) -> alt.Chart:
    data = (
        rides_df.groupby("city")["actual_profit"]
        .sum()
        .fillna(0)
        .reset_index(name="Profit")
    )
    return _single_series_bar(data, "city", "Profit", "Profit by city")


def expense_by_trip_type_chart(rides_df: pd.DataFrame) -> alt.Chart:
    data = (
        rides_df.groupby("trip_type")[["fuel_cost", "maintenance_cost", "tolls", "airport_fee"]]
        .sum()
        .reset_index()
        .melt(id_vars="trip_type", var_name="Cost type", value_name="Amount")
    )
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("trip_type:N", title="", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Amount:Q", title=""),
            color=alt.Color("Cost type:N", scale=COLOR_SCALE),
            xOffset="Cost type:N",
            tooltip=["trip_type", "Cost type", alt.Tooltip("Amount:Q", format=",.2f")],
        )
        .properties(height=CHART_HEIGHT, title="Expense by trip type")
    )
    return _base_chart(chart)


def avg_profit_per_mile_chart(rides_df: pd.DataFrame) -> alt.Chart:
    data = (
        rides_df.groupby("trip_type")[["profit_per_customer_mile", "profit_per_expense_mile"]]
        .mean()
        .reset_index()
        .melt(id_vars="trip_type", var_name="Metric", value_name="Profit per mile")
    )
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("trip_type:N", title="", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Profit per mile:Q", title=""),
            color=alt.Color("Metric:N", scale=COLOR_SCALE),
            xOffset="Metric:N",
            tooltip=["trip_type", "Metric", alt.Tooltip("Profit per mile:Q", format=",.2f")],
        )
        .properties(height=CHART_HEIGHT, title="Avg profit per mile")
    )
    return _base_chart(chart)
