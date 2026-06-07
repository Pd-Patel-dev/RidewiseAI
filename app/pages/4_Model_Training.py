import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib

import streamlit as st

import src.ml.train_model as train_model_module
import src.ml.training_progress as training_progress_module

importlib.reload(train_model_module)
importlib.reload(training_progress_module)

from src.database.db import init_db
from src.database.ride_repository import get_all_rides
from src.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    get_missing_columns,
)
from src.ml.predict_fare import predict_fare
from src.ml.train_model import MODEL_PATH
from src.ml.training_progress import train_model_with_progress
from src.ml.training_results import load_training_results
from src.pricing.rule_based import TRIP_TYPES

st.set_page_config(page_title="Model Training", page_icon="🤖", layout="wide")
init_db()


def show_model_performance(results: dict) -> None:
    """Display the last training performance metrics."""
    st.markdown("#### Model performance (last training)")

    if results.get("small_dataset"):
        st.warning(
            "Small dataset — MAE and RMSE were calculated on training data only "
            "(no separate test split)."
        )

    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("MAE", f"${results['mae']:.2f}")
    metric_col2.metric("RMSE", f"${results['rmse']:.2f}")
    metric_col3.metric("Rides used", results["rides_used"])
    metric_col4.metric("Train rows", results.get("train_rows", results["rides_used"]))
    metric_col5.metric("Test rows", results.get("test_rows", "—"))

    detail_col1, detail_col2, detail_col3 = st.columns(3)
    detail_col1.metric(
        "Model",
        f"Random Forest ({results.get('n_estimators', 100)} trees)",
    )
    detail_col2.metric("Data source", results.get("data_source", "Saved rides"))
    detail_col3.metric("Last trained", results.get("trained_at", "—"))

    st.markdown("**Features used for training**")
    st.write(f"Numeric: {', '.join(results.get('numeric_features', NUMERIC_FEATURES))}")
    st.write(
        f"Categorical: {', '.join(results.get('categorical_features', CATEGORICAL_FEATURES))}"
    )
    st.write(f"Target: `{results.get('target', TARGET_COLUMN)}`")
    st.caption(f"Model saved to: `{results.get('model_path', MODEL_PATH)}`")


st.title("Model Training")
st.caption(
    "Train a Random Forest model on your saved rides to predict fares using machine learning."
)

last_results = load_training_results()
if last_results:
    show_model_performance(last_results)
    st.divider()

rides_df = get_all_rides()
trainable_rides = rides_df[rides_df["fare_charged"] > 0] if not rides_df.empty else rides_df

st.markdown("#### Training data")
col1, col2, col3 = st.columns(3)
col1.metric("Total saved rides", len(rides_df))
col2.metric("Rides with fare charged", len(trainable_rides))
col3.metric(
    "Model status",
    "Ready" if MODEL_PATH.exists() else "Not trained",
)

st.markdown("**Features used**")
st.write(f"Numeric: {', '.join(NUMERIC_FEATURES)}")
st.write(f"Categorical: {', '.join(CATEGORICAL_FEATURES)}")
st.write(f"Target: `{TARGET_COLUMN}`")

if rides_df.empty:
    st.info("No rides saved yet. Go to **Fare Calculator**, save a few rides, then come back here.")
elif trainable_rides.empty:
    st.warning(
        "You have saved rides, but none have a **fare charged** value. "
        "Enter fare charged when saving rides so the model can learn."
    )
else:
    missing_columns = get_missing_columns(trainable_rides)

    if missing_columns:
        st.error(
            "Cannot train yet. Missing required columns: "
            + ", ".join(missing_columns)
        )
    else:
        preview_columns = [
            column
            for column in NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
            if column in trainable_rides.columns
        ]

        with st.expander("Preview training data"):
            st.dataframe(
                trainable_rides[preview_columns],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        if st.button("Train Model", type="primary", use_container_width=True):
            try:
                train_model_with_progress()
                st.success("Model trained and saved successfully.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

st.divider()
st.markdown("#### Test prediction")

test_col1, test_col2 = st.columns(2)
with test_col1:
    test_trip_type = st.selectbox("Trip type", TRIP_TYPES, key="ml_trip_type")
    test_miles = st.number_input("One-way miles", min_value=0.1, value=10.0, key="ml_miles")
    test_mpg = st.number_input("MPG", min_value=1.0, value=25.0, key="ml_mpg")
    test_gas = st.number_input("Gas price", min_value=0.1, value=3.50, key="ml_gas")
with test_col2:
    test_waiting = st.number_input("Waiting minutes", min_value=0.0, value=0.0, key="ml_wait")
    test_airport = st.toggle("Airport trip", key="ml_airport")

if st.button("Predict Fare", use_container_width=True):
    prediction = predict_fare(
        {
            "trip_type": test_trip_type,
            "one_way_miles": test_miles,
            "mpg": test_mpg,
            "gas_price": test_gas,
            "waiting_minutes": test_waiting,
            "is_airport": test_airport,
        }
    )

    st.metric("Predicted fare", f"${prediction['predicted_fare']:.2f}")
    if prediction["used_fallback"]:
        st.warning(prediction["message"])
    else:
        st.success(prediction["message"])
