import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib

import streamlit as st
import pandas as pd

import src.ml.train_model as train_model_module
import src.ml.training_progress as training_progress_module

importlib.reload(train_model_module)
importlib.reload(training_progress_module)

from src.data.upload_preprocessor import (
    PROCESSED_OUTPUT_PATH,
    convert_uploaded_dataset,
    load_uploaded_file,
    save_converted_dataset,
    save_uploaded_file,
)
from src.ml.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET_COLUMN
from src.ml.train_model import MODEL_PATH, UPLOADED_TRAINING_CSV
from src.ml.training_progress import train_model_with_progress
from src.ml.training_results import save_training_results

st.set_page_config(page_title="Upload Real Dataset", page_icon="📂", layout="wide")

st.title("Upload Real Dataset")
st.caption(
    "Upload NYC Yellow Taxi (.parquet), Chicago Taxi CSV, or Chicago TNP CSV/JSON. "
    "The app converts it into RideWise AI training format automatically."
)

PREVIEW_ROWS = 100

with st.sidebar:
    st.markdown("#### Conversion settings")
    mpg = st.number_input("MPG", min_value=1.0, value=23.0, step=0.1)
    gas_price = st.number_input("Gas price ($)", min_value=0.1, value=3.96, step=0.01)
    avg_speed_mph = st.number_input("Average speed (MPH)", min_value=1.0, value=25.0, step=1.0)
    long_distance_miles = st.number_input(
        "Long-distance threshold (miles)", min_value=1.0, value=40.0, step=1.0
    )
    max_miles = st.number_input("Maximum miles filter", min_value=1.0, value=300.0, step=1.0)
    max_fare = st.number_input("Maximum fare filter ($)", min_value=1.0, value=1000.0, step=1.0)

uploaded_file = st.file_uploader(
    "Choose a dataset file",
    type=["csv", "json", "parquet"],
    help="Supported: NYC Yellow Taxi .parquet, Chicago Taxi/TNP .csv or .json",
)

if uploaded_file is not None:
    file_signature = f"{uploaded_file.name}:{uploaded_file.size}"
    if st.session_state.get("upload_file_signature") != file_signature:
        with st.spinner("Saving and converting uploaded dataset..."):
            try:
                upload_path = save_uploaded_file(uploaded_file.getvalue(), uploaded_file.name)
                raw_df = load_uploaded_file(upload_path)
                conversion = convert_uploaded_dataset(
                    raw_df,
                    mpg=mpg,
                    gas_price=gas_price,
                    avg_speed_mph=avg_speed_mph,
                    long_distance_miles=long_distance_miles,
                    max_miles=max_miles,
                    max_fare=max_fare,
                )
                save_converted_dataset(conversion["converted_df"], PROCESSED_OUTPUT_PATH)

                st.session_state["upload_file_signature"] = file_signature
                st.session_state["upload_path"] = str(upload_path)
                st.session_state["raw_preview_df"] = raw_df.head(PREVIEW_ROWS)
                st.session_state["raw_row_count"] = conversion["raw_row_count"]
                st.session_state["conversion"] = conversion
                st.session_state.pop("upload_training_results", None)
            except ValueError as error:
                st.error(str(error))
                st.session_state.pop("conversion", None)

if "conversion" in st.session_state:
    conversion = st.session_state["conversion"]
    converted_df = conversion["converted_df"]

    st.success(
        "Dataset converted successfully and saved to "
        f"`{PROCESSED_OUTPUT_PATH}`"
    )

    st.markdown("#### Conversion summary")
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("Rows before conversion", conversion["raw_row_count"])
    summary_col2.metric("Rows after cleaning", conversion["converted_row_count"])
    summary_col3.metric("Dataset type detected", conversion["dataset_type"].replace("_", " ").title())
    summary_col4.metric("Saved upload file", Path(st.session_state["upload_path"]).name)

    st.markdown("**Final columns used for model training**")
    st.write(", ".join(conversion["columns"]))
    st.write(f"Numeric: {', '.join(NUMERIC_FEATURES)}")
    st.write(f"Categorical: {', '.join(CATEGORICAL_FEATURES)}")
    st.write(f"Target: `{TARGET_COLUMN}`")

    st.markdown("**Trip type counts**")
    trip_type_df = pd.DataFrame(
        {
            "trip_type": list(conversion["trip_type_counts"].keys()),
            "count": list(conversion["trip_type_counts"].values()),
        }
    )
    st.dataframe(trip_type_df, use_container_width=True, hide_index=True)

    preview_col1, preview_col2 = st.columns(2)
    with preview_col1:
        st.markdown(f"**Raw uploaded data preview** (first {PREVIEW_ROWS} rows)")
        st.dataframe(
            st.session_state["raw_preview_df"],
            use_container_width=True,
            hide_index=True,
        )
    with preview_col2:
        st.markdown(f"**Converted training data preview** (first {PREVIEW_ROWS} rows)")
        st.dataframe(
            converted_df.head(PREVIEW_ROWS),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button("Train Model Using Uploaded Dataset", type="primary", use_container_width=True):
            try:
                results = train_model_with_progress(csv_path=str(UPLOADED_TRAINING_CSV))
                save_training_results(results, data_source="Uploaded dataset")
                st.session_state["upload_training_results"] = results
                st.success("Model trained and saved to models/fare_model.pkl")
            except ValueError as error:
                st.error(str(error))

    with action_col2:
        csv_bytes = converted_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Converted Training CSV",
            data=csv_bytes,
            file_name="ridewiseai_training_uploaded.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if "upload_training_results" in st.session_state:
        results = st.session_state["upload_training_results"]
        st.markdown("#### Training results")
        if results["small_dataset"]:
            st.warning("Small dataset — metrics are calculated on training data only.")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Rides used", results["rides_used"])
        metric_col2.metric("MAE", f"${results['mae']:.2f}")
        metric_col3.metric("RMSE", f"${results['rmse']:.2f}")
        st.caption(f"Model saved to: `{results['model_path']}`")
        st.caption(f"Model status: {'Ready' if MODEL_PATH.exists() else 'Not found'}")

else:
    st.info(
        "Upload a `.csv`, `.json`, or `.parquet` file to convert it into RideWise AI "
        "training format. Converted data is saved to "
        f"`{PROCESSED_OUTPUT_PATH}`."
    )
