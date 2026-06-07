import pandas as pd
from sqlalchemy import select

from src.database.db import get_session
from src.database.models import Ride


def save_ride(ride_data: dict) -> Ride:
    """Save one ride from a dictionary and return the saved record."""
    session = get_session()
    try:
        ride = Ride(**ride_data)
        session.add(ride)
        session.commit()
        session.refresh(ride)
        return ride
    finally:
        session.close()


def get_all_rides() -> pd.DataFrame:
    """Load all rides from the database as a pandas DataFrame."""
    session = get_session()
    try:
        statement = select(Ride).order_by(Ride.created_at.desc())
        rides = list(session.scalars(statement).all())
    finally:
        session.close()

    if not rides:
        return pd.DataFrame()

    records = [
        {
            "id": ride.id,
            "created_at": ride.created_at,
            "trip_type": ride.trip_type,
            "one_way_miles": ride.one_way_miles,
            "customer_miles": ride.customer_miles,
            "expense_miles": ride.expense_miles,
            "mpg": ride.mpg,
            "gas_price": ride.gas_price,
            "trip_minutes": ride.trip_minutes,
            "waiting_minutes": ride.waiting_minutes,
            "city": ride.city,
            "is_airport": ride.is_airport,
            "tolls": ride.tolls,
            "airport_fee": ride.airport_fee,
            "fare_charged": ride.fare_charged,
            "fuel_cost": ride.fuel_cost,
            "maintenance_cost": ride.maintenance_cost,
            "total_expense": ride.total_expense,
            "recommended_fare": ride.recommended_fare,
            "actual_profit": ride.actual_profit,
            "profit_per_expense_mile": ride.profit_per_expense_mile,
            "profit_per_customer_mile": ride.profit_per_customer_mile,
        }
        for ride in rides
    ]

    return pd.DataFrame(records)
