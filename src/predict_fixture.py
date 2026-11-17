"""Leakage-aware feature assembly and probability inference for manual fixtures."""

from __future__ import annotations

import sys
from collections import deque
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_features import (  # noqa: E402
    HOME_ADVANTAGE_ELO,
    INITIAL_ELO,
    RECENT_WINDOW,
    per_match_summary,
    recent_summary,
    venue_points,
)
from evaluate_models import CLASS_ORDER, FEATURE_SETS  # noqa: E402


def _state_or_cold_start(team_states: dict, team_key: str) -> tuple[dict, bool]:
    state = team_states.get(team_key)
    if not state:
        return {}, True
    return state, int(state.get("played", 0)) == 0


def build_fixture_features(
    team_states: dict,
    home_key: str,
    away_key: str,
) -> tuple[dict[str, float], dict[str, bool]]:
    """Build the same pre-match numeric features as build_features.py.

    This function consumes a state snapshot made after all results on its as-of
    date. Callers must require the requested fixture date to be strictly later
    than that snapshot date, so no same-day or later outcome can enter.
    """
    if not home_key or not away_key:
        raise ValueError("Choose both a home team and an away team")
    if home_key == away_key:
        raise ValueError("Home and away teams must be different")

    home, home_cold = _state_or_cold_start(team_states, home_key)
    away, away_cold = _state_or_cold_start(team_states, away_key)
    feature: dict[str, float] = {}
    feature.update(per_match_summary(home, "home"))
    feature.update(per_match_summary(away, "away"))
    feature.update(venue_points(home, "home", "home_team"))
    feature.update(venue_points(away, "away", "away_team"))

    home_elo = float(home.get("elo_rating", INITIAL_ELO))
    away_elo = float(away.get("elo_rating", INITIAL_ELO))
    feature.update({
        "elo_home": home_elo,
        "elo_away": away_elo,
        "elo_difference": home_elo - away_elo + HOME_ADVANTAGE_ELO,
    })

    def recent_deque(state: dict) -> deque:
        values = [
            (float(item["points"]), float(item["goal_difference"]))
            for item in state.get("recent_results", [])
        ]
        return deque(values[-RECENT_WINDOW:], maxlen=RECENT_WINDOW)

    feature.update(recent_summary(recent_deque(home), "home"))
    feature.update(recent_summary(recent_deque(away), "away"))
    feature["recent5_points_difference"] = (
        feature["home_recent5_points_per_match"] - feature["away_recent5_points_per_match"]
        if pd.notna(feature["home_recent5_points_per_match"])
        and pd.notna(feature["away_recent5_points_per_match"])
        else np.nan
    )
    feature["recent5_goal_diff_difference"] = (
        feature["home_recent5_goal_diff_per_match"] - feature["away_recent5_goal_diff_per_match"]
        if pd.notna(feature["home_recent5_goal_diff_per_match"])
        and pd.notna(feature["away_recent5_goal_diff_per_match"])
        else np.nan
    )
    return feature, {"home": home_cold, "away": away_cold}


def predict_fixture(
    *,
    model_name: str,
    model,
    team_states: dict,
    home_key: str,
    away_key: str,
    prediction_date: date | str,
    state_as_of_date: date | str,
) -> dict:
    """Return real predict_proba results and the exact model input row."""
    key = model_name if model_name.startswith("Model ") else f"Model {model_name}"
    if key not in FEATURE_SETS:
        raise ValueError("Select Model A, Model B, or Model C")

    target_date = pd.Timestamp(prediction_date).date()
    cutoff_date = pd.Timestamp(state_as_of_date).date()
    if target_date <= cutoff_date:
        raise ValueError(
            f"Prediction date must be after the available team-state cutoff ({cutoff_date})."
        )

    features, cold_start = build_fixture_features(team_states, home_key, away_key)
    feature_names = FEATURE_SETS[key]
    row = pd.DataFrame([{name: features.get(name, np.nan) for name in feature_names}], columns=feature_names)
    raw = np.asarray(model.predict_proba(row), dtype=float)
    model_classes = list(model.classes_)
    if raw.shape != (1, len(model_classes)):
        raise ValueError(f"Unexpected predict_proba shape: {raw.shape}")
    if set(model_classes) != set(CLASS_ORDER):
        raise ValueError(f"Model classes do not match the required H/D/A labels: {model_classes}")
    probabilities = raw[0, [model_classes.index(label) for label in CLASS_ORDER]]
    if not np.isfinite(probabilities).all() or not np.isclose(probabilities.sum(), 1.0, atol=1e-8):
        raise ValueError("Model returned invalid H/D/A probabilities")

    return {
        "model": key,
        "prediction_date": target_date.isoformat(),
        "state_as_of_date": cutoff_date.isoformat(),
        "home_key": home_key,
        "away_key": away_key,
        "predicted": CLASS_ORDER[int(np.argmax(probabilities))],
        "probabilities": {label: float(probabilities[i]) for i, label in enumerate(CLASS_ORDER)},
        "features": {name: (float(row.iloc[0][name]) if pd.notna(row.iloc[0][name]) else np.nan)
                     for name in feature_names},
        "cold_start": cold_start,
    }
