"""

Train a fare prediction model from saved ride history.



Run from the project root:

    py -m src.ml.train_model

    py -m src.ml.train_model --csv data/ridewiseai_training.csv

"""



from __future__ import annotations



from collections.abc import Callable

from pathlib import Path



import joblib

import numpy as np

import pandas as pd

from sklearn.compose import ColumnTransformer

from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import mean_absolute_error, mean_squared_error

from sklearn.model_selection import train_test_split

from sklearn.pipeline import Pipeline

from sklearn.preprocessing import OneHotEncoder



from src.database.ride_repository import get_all_rides

from src.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    get_missing_columns,
    prepare_features,
    get_target_series,
)
from src.ml.training_results import save_training_results



PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = PROJECT_ROOT / "models" / "fare_model.pkl"

UPLOADED_TRAINING_CSV = (

    PROJECT_ROOT / "data" / "processed" / "ridewiseai_training_uploaded.csv"

)



N_ESTIMATORS = 100

TREE_BATCH_SIZE = 10



ProgressCallback = Callable[[float, str], None]





def load_training_data(csv_path: str | None = None) -> pd.DataFrame:

    """Load rides from CSV if provided, otherwise from SQLite."""

    if csv_path:

        return pd.read_csv(csv_path)

    return get_all_rides()





def build_pipeline() -> Pipeline:

    """Create preprocessing + Random Forest pipeline."""

    preprocessor = ColumnTransformer(

        transformers=[

            ("numeric", "passthrough", NUMERIC_FEATURES),

            (

                "category",

                OneHotEncoder(handle_unknown="ignore"),

                CATEGORICAL_FEATURES,

            ),

        ]

    )



    return Pipeline(

        steps=[

            ("preprocessor", preprocessor),

            (

                "model",

                RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=42),

            ),

        ]

    )





def _report_progress(

    progress_callback: ProgressCallback | None,

    percent: float,

    message: str,

) -> None:

    if progress_callback is not None:

        progress_callback(percent, message)





def _fit_random_forest_with_progress(

    model: RandomForestRegressor,

    features: pd.DataFrame,

    target: pd.Series,

    progress_callback: ProgressCallback | None,

    progress_start: float,

    progress_end: float,

) -> None:

    """Fit the forest in batches so the UI can show tree-by-tree progress."""

    total_trees = model.n_estimators

    batch_size = max(1, min(TREE_BATCH_SIZE, total_trees))



    model.set_params(warm_start=True, n_estimators=0)



    trees_fitted = 0

    while trees_fitted < total_trees:

        trees_fitted = min(trees_fitted + batch_size, total_trees)

        model.n_estimators = trees_fitted

        model.fit(features, target)



        fraction = trees_fitted / total_trees

        percent = progress_start + (progress_end - progress_start) * fraction

        _report_progress(

            progress_callback,

            percent,

            f"Training Random Forest: {trees_fitted}/{total_trees} trees...",

        )





def train_model(
    csv_path: str | None = None,
    verbose: bool = True,
    progress_callback: ProgressCallback | None = None,
    data_source: str | None = None,
) -> dict:

    """Train the model, save to models/fare_model.pkl, and return metrics."""

    _report_progress(progress_callback, 0.05, "Loading training data...")

    rides_df = load_training_data(csv_path)



    if rides_df.empty:

        if csv_path:

            raise ValueError(f"No ride data found in {csv_path}.")

        raise ValueError("No ride data found. Save rides in the app first.")



    _report_progress(progress_callback, 0.10, "Validating columns...")

    missing_columns = get_missing_columns(rides_df)

    if missing_columns:

        raise ValueError(

            "Missing required columns for training: " + ", ".join(missing_columns)

        )



    target = get_target_series(rides_df)

    valid_rows = target > 0

    rides_df = rides_df[valid_rows].copy()

    target = target[valid_rows]



    if rides_df.empty:

        raise ValueError("No rides with a fare charged found for training.")



    _report_progress(progress_callback, 0.15, "Preparing features...")

    features = prepare_features(rides_df)

    small_dataset = len(rides_df) < 5



    _report_progress(progress_callback, 0.20, "Splitting train and test data...")

    if len(rides_df) >= 5:

        x_train, x_test, y_train, y_test = train_test_split(

            features, target, test_size=0.2, random_state=42

        )

    else:

        x_train, x_test, y_train, y_test = features, features, target, target

        if verbose:

            print("Note: small dataset — metrics are calculated on training data.")



    _report_progress(progress_callback, 0.25, "Building model pipeline...")

    pipeline = build_pipeline()



    _report_progress(progress_callback, 0.30, "Encoding features...")

    preprocessor = pipeline.named_steps["preprocessor"]

    x_train_transformed = preprocessor.fit_transform(x_train, y_train)



    model = pipeline.named_steps["model"]

    _fit_random_forest_with_progress(

        model,

        x_train_transformed,

        y_train,

        progress_callback,

        progress_start=0.35,

        progress_end=0.85,

    )



    _report_progress(progress_callback, 0.90, "Evaluating model...")

    predictions = pipeline.predict(x_test)

    mae = mean_absolute_error(y_test, predictions)

    rmse = np.sqrt(mean_squared_error(y_test, predictions))



    if verbose:

        print(f"Training rides used: {len(rides_df)}")

        print(f"MAE:  ${mae:.2f}")

        print(f"RMSE: ${rmse:.2f}")



    _report_progress(progress_callback, 0.95, "Saving model...")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)



    _report_progress(progress_callback, 1.0, "Training complete!")



    if verbose:

        print(f"Model saved to: {MODEL_PATH}")



    results = {
        "pipeline": pipeline,
        "rides_used": len(rides_df),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "mae": mae,
        "rmse": rmse,
        "small_dataset": small_dataset,
        "n_estimators": N_ESTIMATORS,
        "model_path": str(MODEL_PATH),
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET_COLUMN,
    }

    if data_source is None:
        data_source = Path(csv_path).name if csv_path else "Saved rides"
    save_training_results(results, data_source=data_source)

    return results





def main() -> None:

    import argparse



    parser = argparse.ArgumentParser(description="Train RideWise fare prediction model")

    parser.add_argument(

        "--csv",

        default=None,

        help="Optional CSV path (e.g. data/ridewiseai_training.csv)",

    )

    args = parser.parse_args()

    train_model(args.csv)





if __name__ == "__main__":

    main()


