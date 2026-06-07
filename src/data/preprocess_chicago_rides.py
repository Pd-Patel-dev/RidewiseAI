"""
Download or load Chicago TNP/Taxi ride data and convert it into RideWise AI
training format for the fare prediction model.

Run from the project root:

    python src/data/preprocess_chicago_rides.py --source tnp2025 --limit 5000
    python src/data/preprocess_chicago_rides.py --input data/chicago_rides.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import requests

# Chicago Data Portal Socrata dataset IDs
CHICAGO_DATASETS = {
    "tnp2025": "6dvr-xwnh",
    "tnp2024": "n26f-ihde",
    "taxi2024": "ajtu-isnz",
}

CHICAGO_API_BASE = "https://data.cityofchicago.org/resource"

OUTPUT_COLUMNS = [
    "trip_type",
    "one_way_miles",
    "mpg",
    "gas_price",
    "waiting_minutes",
    "is_airport",
    "fare_charged",
]

MILEAGE_COLUMNS = ["trip_miles", "trip_distance"]
FARE_TOTAL_COLUMNS = ["trip_total"]
FARE_COMPONENT_COLUMNS = [
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


def parse_airport_areas(airport_areas: str) -> set[int]:
    """Convert a comma-separated list like '76,56,64' into integers."""
    areas: set[int] = set()
    for part in airport_areas.split(","):
        part = part.strip()
        if part:
            areas.add(int(part))
    return areas


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


def find_mileage_column(df: pd.DataFrame) -> str | None:
    """Return the first mileage column found in the dataset."""
    for column in MILEAGE_COLUMNS:
        if column in df.columns:
            return column
    return None


def find_fare_source_columns(df: pd.DataFrame) -> tuple[str | None, list[str]]:
    """
    Return (total_fare_column, component_columns).

    Uses trip_total when available, otherwise sums fare-related columns.
    """
    for column in FARE_TOTAL_COLUMNS:
        if column in df.columns:
            return column, []

    component_columns = [column for column in FARE_COMPONENT_COLUMNS if column in df.columns]
    if component_columns:
        return None, component_columns

    return None, []


def download_chicago_data(source: str, limit: int) -> pd.DataFrame:
    """Download rows from the Chicago Data Portal Socrata JSON API."""
    if source not in CHICAGO_DATASETS:
        valid_sources = ", ".join(sorted(CHICAGO_DATASETS))
        raise ValueError(
            f"Unknown source '{source}'. Choose one of: {valid_sources}"
        )

    dataset_id = CHICAGO_DATASETS[source]
    url = f"{CHICAGO_API_BASE}/{dataset_id}.json"

    rows: list[dict] = []
    offset = 0
    page_size = 1000

    print(f"Downloading from Chicago Data Portal ({source}, id={dataset_id})...")

    while len(rows) < limit:
        batch_limit = min(page_size, limit - len(rows))
        params = {"$limit": batch_limit, "$offset": offset}

        try:
            response = requests.get(url, params=params, timeout=180)
            response.raise_for_status()
        except requests.RequestException as error:
            raise ValueError(
                f"Could not download data from Chicago Data Portal: {error}"
            ) from error

        payload = response.json()
        if isinstance(payload, dict) and payload.get("error"):
            message = payload.get("message", "Unknown API error")
            raise ValueError(f"Chicago Data Portal returned an error: {message}")

        if not payload:
            break

        rows.extend(payload)
        print(f"  Downloaded {len(rows):,} rows so far...")

        if len(payload) < batch_limit:
            break

        offset += batch_limit

    if not rows:
        raise ValueError(
            "Downloaded data is empty. Try a different --source or check the API."
        )

    return pd.DataFrame(rows)


def load_local_file(input_path: Path) -> pd.DataFrame:
    """Load a local CSV or JSON file."""
    if not input_path.exists():
        raise ValueError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(input_path)
    if suffix == ".json":
        with input_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            return pd.DataFrame(payload)
        if isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                return pd.DataFrame(payload["data"])
            return pd.DataFrame([payload])

        raise ValueError(
            f"Unsupported JSON structure in {input_path}. Expected a list of records."
        )

    raise ValueError(
        f"Unsupported input file type '{suffix}'. Use a .csv or .json file."
    )


def build_fare_charged(df: pd.DataFrame) -> pd.Series:
    """Create fare_charged from trip_total or fare component columns."""
    total_column, component_columns = find_fare_source_columns(df)

    if total_column:
        return to_numeric_series(df[total_column])

    if not component_columns:
        raise ValueError(
            "No fare column found. Expected one of: "
            + ", ".join(FARE_TOTAL_COLUMNS + FARE_COMPONENT_COLUMNS)
        )

    fare_total = pd.Series(0.0, index=df.index, dtype="float64")
    for column in component_columns:
        fare_total = fare_total.add(to_numeric_series(df[column]).fillna(0), fill_value=0)

    return fare_total


def build_is_airport(
    df: pd.DataFrame,
    airport_areas: set[int],
) -> pd.Series:
    """Mark airport trips when pickup or dropoff community area matches."""
    pickup = pd.to_numeric(df.get("pickup_community_area"), errors="coerce")
    dropoff = pd.to_numeric(df.get("dropoff_community_area"), errors="coerce")

    is_airport = pickup.isin(airport_areas) | dropoff.isin(airport_areas)
    return is_airport.fillna(False).astype(int)


def assign_trip_type(
    one_way_miles: pd.Series,
    is_airport: pd.Series,
    long_distance_miles: float,
) -> pd.Series:
    """Apply simple trip type rules based on distance and airport flag."""
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


def build_waiting_minutes(
    df: pd.DataFrame,
    one_way_miles: pd.Series,
    avg_speed_mph: float,
) -> pd.Series:
    """Estimate waiting time from trip duration minus expected driving time."""
    if "trip_seconds" not in df.columns:
        return pd.Series(0.0, index=df.index)

    trip_minutes = to_numeric_series(df["trip_seconds"]) / 60
    expected_drive_minutes = (one_way_miles / avg_speed_mph) * 60
    waiting_minutes = trip_minutes - expected_drive_minutes
    waiting_minutes = waiting_minutes.clip(lower=0)
    return waiting_minutes.fillna(0)


def convert_to_ridewise_format(
    raw_df: pd.DataFrame,
    mpg: float,
    gas_price: float,
    avg_speed_mph: float,
    airport_areas: set[int],
    long_distance_miles: float,
) -> pd.DataFrame:
    """Map Chicago ride columns into RideWise AI training columns."""
    df = normalize_column_names(raw_df)

    mileage_column = find_mileage_column(df)
    if mileage_column is None:
        raise ValueError(
            "No mileage column found. Expected one of: "
            + ", ".join(MILEAGE_COLUMNS)
        )

    one_way_miles = to_numeric_series(df[mileage_column])
    fare_charged = build_fare_charged(df)
    is_airport = build_is_airport(df, airport_areas)
    waiting_minutes = build_waiting_minutes(df, one_way_miles, avg_speed_mph)
    trip_type = assign_trip_type(one_way_miles, is_airport, long_distance_miles)

    converted = pd.DataFrame(
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

    return converted


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


def print_summary(output_path: Path, df: pd.DataFrame) -> None:
    """Print a beginner-friendly summary after saving the CSV."""
    print("\nSuccess! RideWise AI training dataset created.")
    print(f"Output CSV: {output_path}")
    print(f"Rows saved: {len(df):,}")
    print(f"Columns: {', '.join(df.columns)}")
    print("\nTrip type counts:")
    print(df["trip_type"].value_counts().to_string())
    print("\nPreview (first 5 rows):")
    print(df.head(5).to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Chicago TNP/Taxi data into RideWise AI training CSV"
    )
    parser.add_argument(
        "--source",
        default="tnp2025",
        choices=sorted(CHICAGO_DATASETS.keys()),
        help="Chicago dataset to download when --input is not used",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional local CSV or JSON file instead of downloading",
    )
    parser.add_argument(
        "--output",
        default="data/ridewiseai_training.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Number of rows to download from the API",
    )
    parser.add_argument("--mpg", type=float, default=23, help="Default MPG value")
    parser.add_argument(
        "--gas-price",
        type=float,
        default=3.96,
        help="Default gas price value",
    )
    parser.add_argument(
        "--avg-speed-mph",
        type=float,
        default=25,
        help="Average driving speed used to estimate waiting minutes",
    )
    parser.add_argument(
        "--airport-areas",
        default="76,56,64",
        help="Comma-separated Chicago community area IDs treated as airport areas",
    )
    parser.add_argument(
        "--long-distance-miles",
        type=float,
        default=40,
        help="Minimum miles for long-distance one-way trips",
    )
    parser.add_argument(
        "--max-miles",
        type=float,
        default=300,
        help="Remove trips above this mileage",
    )
    parser.add_argument(
        "--max-fare",
        type=float,
        default=1000,
        help="Remove trips above this fare",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        airport_areas = parse_airport_areas(args.airport_areas)

        if args.input:
            print(f"Loading local file: {args.input}")
            raw_df = load_local_file(Path(args.input))
        else:
            raw_df = download_chicago_data(args.source, args.limit)

        if raw_df.empty:
            raise ValueError("Input data is empty after loading.")

        converted = convert_to_ridewise_format(
            raw_df=raw_df,
            mpg=args.mpg,
            gas_price=args.gas_price,
            avg_speed_mph=args.avg_speed_mph,
            airport_areas=airport_areas,
            long_distance_miles=args.long_distance_miles,
        )

        cleaned = clean_training_data(
            converted,
            max_miles=args.max_miles,
            max_fare=args.max_fare,
        )

        if cleaned.empty:
            raise ValueError(
                "No rows left after cleaning. Try increasing --limit or relaxing filters."
            )

        cleaned.to_csv(output_path, index=False)
        print_summary(output_path, cleaned)
        return 0

    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
