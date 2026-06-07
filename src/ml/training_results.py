"""Save and load the last model training performance summary."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAST_TRAINING_RESULTS_PATH = PROJECT_ROOT / "models" / "last_training_results.json"


def save_training_results(results: dict, data_source: str = "Saved rides") -> None:
    """Persist performance metrics so the app can show them on the next visit."""
    record = {
        "mae": round(float(results["mae"]), 2),
        "rmse": round(float(results["rmse"]), 2),
        "rides_used": int(results["rides_used"]),
        "train_rows": int(results.get("train_rows", results["rides_used"])),
        "test_rows": int(results.get("test_rows", 0)),
        "small_dataset": bool(results["small_dataset"]),
        "n_estimators": int(results.get("n_estimators", 100)),
        "model_path": results["model_path"],
        "numeric_features": results["numeric_features"],
        "categorical_features": results["categorical_features"],
        "target": results["target"],
        "data_source": data_source,
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    LAST_TRAINING_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LAST_TRAINING_RESULTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)


def load_training_results() -> dict | None:
    """Load the last saved training performance summary, if available."""
    if not LAST_TRAINING_RESULTS_PATH.exists():
        return None

    try:
        with LAST_TRAINING_RESULTS_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None
