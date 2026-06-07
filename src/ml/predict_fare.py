"""
Predict fare using the trained ML model.
"""

import joblib

from src.ml.features import prepare_features, ride_dict_to_dataframe
from src.ml.train_model import MODEL_PATH
from src.pricing.rule_based import calculate_rule_based_fare


def _rule_based_fallback(ride_input: dict) -> float:
    """Use rule-based pricing when the ML model is not available."""
    trip_type = ride_input.get("trip_type", "One-way")
    one_way_miles = ride_input.get("one_way_miles", 0)
    mpg = ride_input.get("mpg", 25)
    gas_price = ride_input.get("gas_price", 3.5)
    waiting_minutes = ride_input.get("waiting_minutes", 0)
    tolls = ride_input.get("tolls", 0)
    airport_fee = ride_input.get("airport_fee", 0)
    profit_margin = ride_input.get("profit_margin", 0.30)

    if ride_input.get("is_airport"):
        from config.settings import AIRPORT_FEE

        airport_fee = airport_fee or AIRPORT_FEE

    result = calculate_rule_based_fare(
        trip_type=trip_type,
        one_way_miles=one_way_miles,
        mpg=mpg,
        gas_price=gas_price,
        tolls=tolls,
        airport_fee=airport_fee,
        profit_margin=profit_margin,
        waiting_minutes=waiting_minutes,
    )
    return result["recommended_fare"]


def predict_fare(ride_input: dict) -> dict:
    """
    Predict fare for one ride.

    Returns a dictionary with:
    - predicted_fare
    - used_fallback (True if rule-based pricing was used)
    - message (optional info for the caller)
    """
    if not MODEL_PATH.exists():
        fallback_fare = _rule_based_fallback(ride_input)
        return {
            "predicted_fare": round(fallback_fare, 2),
            "used_fallback": True,
            "message": "ML model not found. Used rule-based recommended fare instead.",
        }

    pipeline = joblib.load(MODEL_PATH)
    feature_row = prepare_features(ride_dict_to_dataframe(ride_input))
    predicted = float(pipeline.predict(feature_row)[0])

    return {
        "predicted_fare": round(predicted, 2),
        "used_fallback": False,
        "message": "Prediction from trained ML model.",
    }
