"""Export the saved project evidence for the static GitHub Pages site.

This script reads existing model/evaluation artifacts. It does not fit models,
change evaluation results, or access a live fixture feed.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "docs" / "site_data"
MODELS = DATA / "models"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def records(path: Path) -> list[dict]:
    return clean(pd.read_csv(path).to_dict(orient="records"))


def latest_team_labels(matches: pd.DataFrame, aliases: pd.DataFrame) -> dict[str, str]:
    source_to_key = dict(zip(aliases.source_name, aliases.team_key))
    appearances = pd.concat([
        matches[["date", "home_team"]].rename(columns={"home_team": "source_name"}),
        matches[["date", "away_team"]].rename(columns={"away_team": "source_name"}),
    ], ignore_index=True)
    appearances["team_key"] = appearances.source_name.map(source_to_key)
    appearances = appearances.dropna(subset=["team_key"]).sort_values("date")
    latest = appearances.groupby("team_key", sort=False).tail(1)
    return dict(zip(latest.team_key, latest.source_name))


def model_parameters(model_path: Path, expected_hash: str) -> dict:
    if sha256(model_path) != expected_hash:
        raise ValueError(f"Saved model hash does not match manifest: {model_path.name}")
    pipeline = joblib.load(model_path)
    imputer = pipeline.named_steps["simpleimputer"]
    scaler = pipeline.named_steps["standardscaler"]
    classifier = pipeline.named_steps["logisticregression"]
    if classifier.coef_.shape[0] != len(classifier.classes_):
        raise ValueError(f"Unexpected multiclass coefficient layout in {model_path.name}")
    return {
        "classes": classifier.classes_.tolist(),
        "features": pipeline.feature_names_in_.tolist(),
        "imputer_medians": imputer.statistics_.tolist(),
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coefficients": classifier.coef_.tolist(),
        "intercept": classifier.intercept_.tolist(),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((MODELS / "prediction_model_manifest.json").read_text(encoding="utf-8"))
    snapshot_path = DATA / "processed" / "team_state_snapshot.json"
    feature_path = DATA / "processed" / "historical_features.csv"
    for path, key in [
        (snapshot_path, "state_snapshot_sha256"),
        (feature_path, "feature_table_sha256"),
    ]:
        if sha256(path) != manifest[key]:
            raise ValueError(f"Input hash does not match inference manifest: {path.name}")

    model_payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "class_order": manifest["class_order"],
        "training_rows": manifest["training_rows"],
        "training_cutoff_season": manifest["training_cutoff_season"],
        "selected_logistic_c": manifest["selected_logistic_c"],
        "historical_state_as_of_date": manifest["historical_state_as_of_date"],
        "source_model_manifest_sha256": sha256(MODELS / "prediction_model_manifest.json"),
        "models": {},
    }
    for name, details in manifest["models"].items():
        model_payload["models"][name] = model_parameters(ROOT / details["path"], details["sha256"])

    matches = pd.read_csv(DATA / "processed" / "ucl_matches.csv", parse_dates=["date"])
    aliases = pd.read_csv(DATA / "metadata" / "team_aliases.csv")
    matches["match_id"] = matches.source_file.str.replace(".txt", "", regex=False) + ":" + matches.source_line.astype(str)
    labels = latest_team_labels(matches, aliases)
    state = json.loads(snapshot_path.read_text(encoding="utf-8"))
    state["team_labels"] = {
        key: labels[key] for key in state["teams"] if key in labels
    }

    predictions = pd.read_csv(DATA / "results" / "predictions.csv")
    predictions = predictions[predictions.period.eq("final_test")].copy()
    predictions = predictions.merge(
        matches[["match_id", "home_team", "away_team", "regulation_home_goals", "regulation_away_goals", "stage"]],
        on="match_id", how="left", validate="many_to_one",
    )
    prediction_fields = [
        "model", "match_id", "season", "date", "competition_phase", "format_era",
        "home_team", "away_team", "actual", "predicted", "p_H", "p_D", "p_A",
        "regulation_home_goals", "regulation_away_goals", "stage",
    ]

    split_counts = pd.read_csv(DATA / "metadata" / "evaluation_split_assignments.csv")
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "title": "UEFA Champions League Match Outcome Predictor",
        "match_rows": int(len(matches)),
        "seasons": sorted(matches.season.unique().tolist()),
        "date_start": matches.date.min().date().isoformat(),
        "date_end": matches.date.max().date().isoformat(),
        "outcome_counts": matches.outcome_90m.value_counts().reindex(["H", "D", "A"], fill_value=0).to_dict(),
        "outcome_names": {"H": "Home win", "D": "Draw", "A": "Away win"},
        "source_manifest": records(DATA / "metadata" / "ucl_source_manifest.csv"),
        "split_counts": {
            "validation_train": int(split_counts.validation_assignment.eq("train").sum()),
            "validation": int(split_counts.validation_assignment.eq("validation").sum()),
            "final_train": int(split_counts.final_assignment.eq("train").sum()),
            "final_test": int(split_counts.final_assignment.eq("test").sum()),
        },
        "metrics": records(DATA / "results" / "metrics.csv"),
        "confusion": records(DATA / "results" / "confusion_matrices.csv"),
        "calibration": records(DATA / "results" / "calibration_bins.csv"),
        "final_test_predictions": clean(predictions[prediction_fields].to_dict(orient="records")),
        "draw_diagnostics": records(DATA / "results" / "validation_draw_diagnostics.csv"),
        "draw_calibration": records(DATA / "results" / "validation_draw_calibration.csv"),
    }
    for name, payload in [
        ("model_parameters.json", model_payload),
        ("team_state.json", state),
        ("research_results.json", summary),
    ]:
        target = OUT / name
        target.write_text(json.dumps(clean(payload), indent=2, allow_nan=False), encoding="utf-8")
        print(f"Wrote {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")

    figure_source = ROOT / "reports" / "figures" / "calibration_test.png"
    if figure_source.exists():
        figure_target = ROOT / "docs" / "assets" / "calibration_test.png"
        figure_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(figure_source, figure_target)
        print(f"Copied saved calibration figure to {figure_target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
