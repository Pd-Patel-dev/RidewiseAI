import pandas as pd

NUMERIC_FEATURES = [
    "one_way_miles",
    "mpg",
    "gas_price",
    "waiting_minutes",
    "is_airport",
]
CATEGORICAL_FEATURES = ["trip_type"]
TARGET_COLUMN = "fare_charged"

ALL_REQUIRED_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def get_missing_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return feature columns that are missing from the DataFrame."""
    return [column for column in FEATURE_COLUMNS if column not in df.columns]


def get_missing_columns(df: pd.DataFrame) -> list[str]:
    """Return all required training columns that are missing."""
    return [column for column in ALL_REQUIRED_COLUMNS if column not in df.columns]


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Select and clean feature columns using the real dataset column names."""
    missing = get_missing_feature_columns(df)
    if missing:
        raise ValueError(
            "Missing required feature columns: " + ", ".join(missing)
        )

    features = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    features["is_airport"] = features["is_airport"].astype(int)
    features["trip_type"] = features["trip_type"].fillna("One-way").astype(str)
    return features


def get_target_series(df: pd.DataFrame) -> pd.Series:
    """Return the fare_charged target column."""
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")
    return df[TARGET_COLUMN]


def ride_dict_to_dataframe(ride_input: dict) -> pd.DataFrame:
    """Convert one ride input dictionary into a single-row DataFrame."""
    is_airport = ride_input.get("is_airport", False)
    if isinstance(is_airport, bool):
        is_airport = int(is_airport)

    row = {
        "one_way_miles": ride_input.get("one_way_miles", 0),
        "mpg": ride_input.get("mpg", 25),
        "gas_price": ride_input.get("gas_price", 3.5),
        "waiting_minutes": ride_input.get("waiting_minutes", 0),
        "is_airport": is_airport,
        "trip_type": ride_input.get("trip_type", "One-way"),
    }
    return pd.DataFrame([row])
