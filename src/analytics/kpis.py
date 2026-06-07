import pandas as pd


def calculate_summary_kpis(df: pd.DataFrame) -> dict:
    """Calculate business KPIs from a rides DataFrame."""
    total_rides = len(df)
    total_revenue = df["fare_charged"].sum()
    total_recommended_fare = df["recommended_fare"].sum()
    total_fuel_cost = df["fuel_cost"].sum()
    total_maintenance_cost = df["maintenance_cost"].sum()
    total_tolls = df["tolls"].sum()
    total_airport_fees = df["airport_fee"].sum()
    total_expense = df["total_expense"].sum()
    total_profit = df["actual_profit"].fillna(0).sum()
    total_customer_miles = df["customer_miles"].sum()
    total_expense_miles = df["expense_miles"].sum()
    total_one_way_miles = df["one_way_miles"].sum()

    profit_per_customer = df["profit_per_customer_mile"].dropna()
    profit_per_expense = df["profit_per_expense_mile"].dropna()

    avg_fare_charged = df["fare_charged"].mean() if total_rides else 0.0
    avg_expense_per_ride = df["total_expense"].mean() if total_rides else 0.0
    avg_profit_per_ride = total_profit / total_rides if total_rides else 0.0
    avg_profit_per_customer_mile = (
        profit_per_customer.mean() if not profit_per_customer.empty else 0.0
    )
    avg_profit_per_expense_mile = (
        profit_per_expense.mean() if not profit_per_expense.empty else 0.0
    )
    cost_per_expense_mile = (
        total_expense / total_expense_miles if total_expense_miles > 0 else 0.0
    )
    profit_margin_pct = (
        (total_profit / total_revenue) * 100 if total_revenue > 0 else 0.0
    )
    airport_trips = int(df["is_airport"].sum())

    return {
        "total_rides": total_rides,
        "total_revenue": total_revenue,
        "total_recommended_fare": total_recommended_fare,
        "total_fuel_cost": total_fuel_cost,
        "total_maintenance_cost": total_maintenance_cost,
        "total_tolls": total_tolls,
        "total_airport_fees": total_airport_fees,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "total_customer_miles": total_customer_miles,
        "total_expense_miles": total_expense_miles,
        "total_one_way_miles": total_one_way_miles,
        "avg_fare_charged": avg_fare_charged,
        "avg_expense_per_ride": avg_expense_per_ride,
        "avg_profit_per_ride": avg_profit_per_ride,
        "avg_profit_per_customer_mile": avg_profit_per_customer_mile,
        "avg_profit_per_expense_mile": avg_profit_per_expense_mile,
        "cost_per_expense_mile": cost_per_expense_mile,
        "profit_margin_pct": profit_margin_pct,
        "airport_trips": airport_trips,
    }
