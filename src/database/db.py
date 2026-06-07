from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "rides.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def _needs_schema_reset() -> bool:
    """Return True if the rides table uses an old column layout."""
    if not DATABASE_PATH.exists():
        return False

    import sqlite3

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(rides)")}
        if not columns:
            return False
        required_columns = {
            "trip_type",
            "one_way_miles",
            "customer_miles",
            "expense_miles",
            "profit_per_expense_mile",
        }
        return not required_columns.issubset(columns)
    finally:
        conn.close()


def init_db() -> None:
    """Create the database file and tables if they do not exist yet."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Import here so Ride is registered with Base before create_all runs
    from src.database import models  # noqa: F401

    if _needs_schema_reset():
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Open a new database session."""
    return SessionLocal()
