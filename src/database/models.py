from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.db import Base


class Ride(Base):
    """One saved trip from the Fare Calculator."""

    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trip_type: Mapped[str] = mapped_column(String(50), nullable=False)
    one_way_miles: Mapped[float] = mapped_column(Float, nullable=False)
    customer_miles: Mapped[float] = mapped_column(Float, nullable=False)
    expense_miles: Mapped[float] = mapped_column(Float, nullable=False)

    mpg: Mapped[float] = mapped_column(Float, nullable=False)
    gas_price: Mapped[float] = mapped_column(Float, nullable=False)
    trip_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    waiting_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    is_airport: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tolls: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    airport_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    fare_charged: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fuel_cost: Mapped[float] = mapped_column(Float, nullable=False)
    maintenance_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_expense: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_fare: Mapped[float] = mapped_column(Float, nullable=False)
    actual_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_per_expense_mile: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_per_customer_mile: Mapped[float | None] = mapped_column(Float, nullable=True)
