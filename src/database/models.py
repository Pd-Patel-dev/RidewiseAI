from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Ride(Base):
    """One row in the rides table — a single completed or planned trip."""

    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    miles: Mapped[float] = mapped_column(Float, nullable=False)
    mpg: Mapped[float] = mapped_column(Float, nullable=False)
    gas_price: Mapped[float] = mapped_column(Float, nullable=False)
    trip_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    waiting_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    is_airport: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tolls: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    airport_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    fare_charged: Mapped[float] = mapped_column(Float, nullable=False)
    rule_based_fare: Mapped[float] = mapped_column(Float, nullable=False)
    ml_predicted_fare: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    profit: Mapped[float] = mapped_column(Float, nullable=False)
