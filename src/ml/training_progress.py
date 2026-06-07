"""Streamlit progress bar helper for ML model training."""

from __future__ import annotations

import streamlit as st

from src.ml.train_model import train_model


def train_model_with_progress(
    csv_path: str | None = None,
    data_source: str = "Saved rides",
) -> dict:
    """Train the fare model, save performance metrics, and update a progress bar."""
    progress_bar = st.progress(0, text="Starting training...")
    status_text = st.empty()

    def update_progress(percent: float, message: str) -> None:
        progress_bar.progress(min(max(percent, 0.0), 1.0), text=message)
        status_text.caption(message)

    try:
        results = train_model(
            csv_path=csv_path,
            verbose=False,
            progress_callback=update_progress,
            data_source=data_source,
        )
        progress_bar.progress(1.0, text="Training complete!")
        status_text.caption("Model saved successfully.")
        return results
    except ValueError:
        progress_bar.empty()
        status_text.empty()
        raise
