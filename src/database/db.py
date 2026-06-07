from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, Ride

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "ridewise.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create the data folder and rides table if they do not exist yet."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def save_ride(
    miles: float,
    mpg: float,
    gas_price: float,
    trip_minutes: float,
    waiting_minutes: float,
    city: str,
    is_airport: bool,
    tolls: float,
    airport_fee: float,
    fare_charged: float,
    rule_based_fare: float,
    total_cost: float,
    profit: float,
    ml_predicted_fare: float | None = None,
) -> Ride:
    """Save one ride to the database and return the saved record."""
    ride = Ride(
        miles=miles,
        mpg=mpg,
        gas_price=gas_price,
        trip_minutes=trip_minutes,
        waiting_minutes=waiting_minutes,
        city=city,
        is_airport=is_airport,
        tolls=tolls,
        airport_fee=airport_fee,
        fare_charged=fare_charged,
        rule_based_fare=rule_based_fare,
        ml_predicted_fare=ml_predicted_fare,
        total_cost=total_cost,
        profit=profit,
    )

    session: Session = SessionLocal()
    try:
        session.add(ride)
        session.commit()
        session.refresh(ride)
        return ride
    finally:
        session.close()


def get_all_rides() -> list[Ride]:
    """Return every saved ride, newest first."""
    session: Session = SessionLocal()
    try:
        statement = select(Ride).order_by(Ride.id.desc())
        return list(session.scalars(statement).all())
    finally:
        session.close()
