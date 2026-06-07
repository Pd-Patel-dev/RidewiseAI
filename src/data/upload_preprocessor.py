"""
Convert uploaded taxi/rideshare files (NYC Yellow Taxi, Chicago Taxi/TNP)
into RideWise AI ML training format.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
PROCESSED_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ridewiseai_training_uploaded.csv"
)

OUTPUT_COLUMNS = [
    "trip_type",
    "one_way_miles",
    "mpg",
    "gas_price",
    "waiting_minutes",
    "is_airport",
    "fare_charged",
]

CHICAGO_AIRPORT_AREAS = {76, 56, 64}
NYC_AIRPORT_RATE_CODES = {2, 3}

NYC_FARE_TOTAL_COLUMNS = ["total_amount"]
NYC_FARE_COMPONENT_COLUMNS = [
    "fare_amount",
    "tip_amount",
    "tolls_amount",
    "extra",
    "airport_fee",
    "congestion_surcharge",
]

CHICAGO_FARE_TOTAL_COLUMNS = ["trip_total"]
CHICAGO_FARE_COMPONENT_COLUMNS = [
    "fare",
    "tips",
    "tip",
    "tolls",
    "extras",
    "additional_charges",
]


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and replace spaces with underscores."""
    cleaned = df.copy()
    cleaned.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in cleaned.columns
    ]
    return cleaned


def to_numeric_series(series: pd.Series) -> pd.Series:
    """Convert strings with currency symbols into numeric values."""
    if series.dtype == object:
        cleaned = (
            series.astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def assign_trip_type(
    one_way_miles: pd.Series,
    is_airport: pd.Series,
    long_distance_miles: float,
) -> pd.Series:
    """Apply trip type rules based on distance and airport flag."""
    trip_type = pd.Series("Standard one-way", index=one_way_miles.index, dtype="object")

    not_airport = is_airport != 1
    trip_type.loc[not_airport & (one_way_miles >= long_distance_miles)] = (
        "Long-distance one-way"
    )
    trip_type.loc[
        not_airport
        & (one_way_miles < long_distance_miles)
        & (one_way_miles <= 10)
    ] = "Local one-way"
    trip_type.loc[is_airport == 1] = "Airport trip"

    return trip_type


def clean_training_data(
    df: pd.DataFrame,
    max_miles: float,
    max_fare: float,
) -> pd.DataFrame:
    """Apply filtering rules and keep only the final training columns."""
    cleaned = df.copy()

    cleaned = cleaned[cleaned["one_way_miles"] > 0]
    cleaned = cleaned[cleaned["fare_charged"] > 0]
    cleaned = cleaned[cleaned["one_way_miles"] <= max_miles]
    cleaned = cleaned[cleaned["fare_charged"] <= max_fare]
    cleaned = cleaned[cleaned["mpg"] > 0]
    cleaned = cleaned[cleaned["gas_price"] > 0]

    cleaned = cleaned.dropna()
    cleaned = cleaned.drop_duplicates()

    numeric_columns = [
        "one_way_miles",
        "mpg",
        "gas_price",
        "waiting_minutes",
        "is_airport",
        "fare_charged",
    ]
    for column in numeric_columns:
        cleaned[column] = cleaned[column].round(2)

    return cleaned[OUTPUT_COLUMNS].reset_index(drop=True)


def build_fare_from_columns(
    df: pd.DataFrame,
    total_columns: list[str],
    component_columns: list[str],
    error_message: str,
) -> pd.Series:
    """Build fare_charged from a total column or sum of component columns."""
    for column in total_columns:
        if column in df.columns:
            return to_numeric_series(df[column])

    available_components = [column for column in component_columns if column in df.columns]
    if not available_components:
        raise ValueError(error_message)

    fare_total = pd.Series(0.0, index=df.index, dtype="float64")
    for column in available_components:
        fare_total = fare_total.add(to_numeric_series(df[column]).fillna(0), fill_value=0)

    return fare_total


def load_uploaded_file(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV, JSON, or Parquet file from disk."""
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"Input file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            return pd.DataFrame(payload)
        if isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                return pd.DataFrame(payload["data"])
            return pd.DataFrame([payload])

        raise ValueError(
            f"Unsupported JSON structure in {path}. Expected a list of records."
        )
    if suffix == ".parquet":
        return pd.read_parquet(path)

    raise ValueError(
        f"Unsupported file type '{suffix}'. Upload a .csv, .json, or .parquet file."
    )


def detect_dataset_type(df: pd.DataFrame) -> str:
    """Detect whether the upload looks like NYC Yellow Taxi or Chicago data."""
    columns = set(normalize_column_names(df).columns)

    nyc_markers = {
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "fare_amount",
        "total_amount",
    }
    if len(nyc_markers.intersection(columns)) >= 2:
        return "nyc_yellow_taxi"
    if "trip_distance" in columns and "fare_amount" in columns:
        return "nyc_yellow_taxi"

    chicago_markers = {
        "trip_miles",
        "pickup_community_area",
        "dropoff_community_area",
        "trip_total",
    }
    if len(chicago_markers.intersection(columns)) >= 2:
        return "chicago"
    if "trip_miles" in columns:
        return "chicago"

    raise ValueError(
        "Could not detect dataset type. Upload NYC Yellow Taxi (.parquet) or "
        "Chicago Taxi/TNP (.csv/.json) data with mileage and fare columns."
    )


def convert_nyc_yellow_taxi(
    df: pd.DataFrame,
    mpg: float,
    gas_price: float,
    avg_speed_mph: float,
    long_distance_miles: float,
    max_miles: float,
    max_fare: float,
) -> pd.DataFrame:
    """Convert NYC Yellow Taxi columns into RideWise AI training columns."""
    data = normalize_column_names(df)

    if "trip_distance" not in data.columns:
        raise ValueError(
            "No mileage column found for NYC data. Expected column: trip_distance"
        )

    one_way_miles = to_numeric_series(data["trip_distance"])
    fare_charged = build_fare_from_columns(
        data,
        NYC_FARE_TOTAL_COLUMNS,
        NYC_FARE_COMPONENT_COLUMNS,
        "No fare column found for NYC data. Expected total_amount or fare_amount.",
    )

    if "airport_fee" in data.columns:
        airport_fee = to_numeric_series(data["airport_fee"]).fillna(0)
    else:
        airport_fee = pd.Series(0.0, index=data.index)

    if "ratecodeid" in data.columns:
        rate_code = to_numeric_series(data["ratecodeid"]).fillna(0)
    else:
        rate_code = pd.Series(0.0, index=data.index)

    is_airport = ((airport_fee > 0) | rate_code.isin(NYC_AIRPORT_RATE_CODES)).astype(int)

    if (
        "tpep_pickup_datetime" in data.columns
        and "tpep_dropoff_datetime" in data.columns
    ):
        pickup = pd.to_datetime(data["tpep_pickup_datetime"], errors="coerce")
        dropoff = pd.to_datetime(data["tpep_dropoff_datetime"], errors="coerce")
        trip_minutes = (dropoff - pickup).dt.total_seconds() / 60
        expected_drive_minutes = (one_way_miles / avg_speed_mph) * 60
        waiting_minutes = (trip_minutes - expected_drive_minutes).clip(lower=0).fillna(0)
    else:
        waiting_minutes = pd.Series(0.0, index=data.index)

    trip_type = assign_trip_type(one_way_miles, is_airport, long_distance_miles)

    mapped = pd.DataFrame(
        {
            "trip_type": trip_type,
            "one_way_miles": one_way_miles,
            "mpg": mpg,
            "gas_price": gas_price,
            "waiting_minutes": waiting_minutes,
            "is_airport": is_airport,
            "fare_charged": fare_charged,
        }
    )

    return clean_training_data(mapped, max_miles=max_miles, max_fare=max_fare)


def convert_chicago_rides(
    df: pd.DataFrame,
    mpg: float,
    gas_price: float,
    avg_speed_mph: float,
    long_distance_miles: float,
    max_miles: float,
    max_fare: float,
) -> pd.DataFrame:
    """Convert Chicago Taxi/TNP columns into RideWise AI training columns."""
    data = normalize_column_names(df)

    if "trip_miles" not in data.columns:
        raise ValueError(
            "No mileage column found for Chicago data. Expected column: trip_miles"
        )

    one_way_miles = to_numeric_series(data["trip_miles"])
    fare_charged = build_fare_from_columns(
        data,
        CHICAGO_FARE_TOTAL_COLUMNS,
        CHICAGO_FARE_COMPONENT_COLUMNS,
        "No fare column found for Chicago data. Expected trip_total or fare.",
    )

    pickup = pd.to_numeric(data.get("pickup_community_area"), errors="coerce")
    dropoff = pd.to_numeric(data.get("dropoff_community_area"), errors="coerce")
    is_airport = (
        pickup.isin(CHICAGO_AIRPORT_AREAS) | dropoff.isin(CHICAGO_AIRPORT_AREAS)
    ).fillna(False).astype(int)

    if "trip_seconds" in data.columns:
        trip_minutes = to_numeric_series(data["trip_seconds"]) / 60
        expected_drive_minutes = (one_way_miles / avg_speed_mph) * 60
        waiting_minutes = (trip_minutes - expected_drive_minutes).clip(lower=0).fillna(0)
    else:
        waiting_minutes = pd.Series(0.0, index=data.index)

    trip_type = assign_trip_type(one_way_miles, is_airport, long_distance_miles)

    mapped = pd.DataFrame(
        {
            "trip_type": trip_type,
            "one_way_miles": one_way_miles,
            "mpg": mpg,
            "gas_price": gas_price,
            "waiting_minutes": waiting_minutes,
            "is_airport": is_airport,
            "fare_charged": fare_charged,
        }
    )

    return clean_training_data(mapped, max_miles=max_miles, max_fare=max_fare)


def convert_uploaded_dataset(
    df: pd.DataFrame,
    mpg: float,
    gas_price: float,
    avg_speed_mph: float,
    long_distance_miles: float,
    max_miles: float,
    max_fare: float,
) -> dict:
    """
    Detect dataset type, convert to RideWise format, and return summary info.

    Raises ValueError with a clear message when conversion fails.
    """
    if df.empty:
        raise ValueError("Uploaded file is empty.")

    raw_df = normalize_column_names(df)
    raw_row_count = len(raw_df)
    dataset_type = detect_dataset_type(raw_df)

    if dataset_type == "nyc_yellow_taxi":
        converted_df = convert_nyc_yellow_taxi(
            raw_df,
            mpg=mpg,
            gas_price=gas_price,
            avg_speed_mph=avg_speed_mph,
            long_distance_miles=long_distance_miles,
            max_miles=max_miles,
            max_fare=max_fare,
        )
    else:
        converted_df = convert_chicago_rides(
            raw_df,
            mpg=mpg,
            gas_price=gas_price,
            avg_speed_mph=avg_speed_mph,
            long_distance_miles=long_distance_miles,
            max_miles=max_miles,
            max_fare=max_fare,
        )

    if converted_df.empty:
        raise ValueError(
            "Converted dataset has 0 rows after cleaning. "
            "Try relaxing the max miles or max fare filters."
        )

    return {
        "dataset_type": dataset_type,
        "raw_row_count": raw_row_count,
        "converted_row_count": len(converted_df),
        "converted_df": converted_df,
        "trip_type_counts": converted_df["trip_type"].value_counts().to_dict(),
        "columns": OUTPUT_COLUMNS,
    }


def save_converted_dataset(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Save the converted training dataset to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def save_uploaded_file(uploaded_bytes: bytes, filename: str) -> Path:
    """Save the original uploaded file to data/uploads/."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_path = UPLOADS_DIR / filename
    upload_path.write_bytes(uploaded_bytes)
    return upload_path
