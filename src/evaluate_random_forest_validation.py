"""Supplementary Random Forest validation experiment; never writes frozen evaluation files."""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evaluate_models import CLASS_ORDER, FEATURE_SETS, metric_row  # noqa: E402

FEATURE_PATH = ROOT / "data/processed/historical_features.csv"
METRICS_PATH = ROOT / "data/results/metrics.csv"
OUT = ROOT / "reports/random_forest_validation"
TRAIN_SEASONS = ["2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21"]
VALIDATION_SEASONS = ["2021-22", "2022-23"]
RF_CONFIG = {
    "n_estimators": 500,
    "max_features": "sqrt",
    "min_samples_leaf": 5,
    "max_depth": None,
    "class_weight": None,
    "random_state": 335,
    "n_jobs": -1,
}
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def ordered_probabilities(model, X):
    raw = model.predict_proba(X)
    model_classes = list(model.named_steps["randomforestclassifier"].classes_)
    if set(model_classes) != set(CLASS_ORDER):
        raise ValueError(f"Training classes are incomplete: {model_classes}")
    ordered = raw[:, [model_classes.index(c) for c in CLASS_ORDER]]
    if ordered.shape != (len(X), len(CLASS_ORDER)) or not np.isfinite(ordered).all():
        raise ValueError("predict_proba returned invalid dimensions or non-finite values")
    if not np.allclose(ordered.sum(axis=1), 1.0, atol=1e-8, rtol=0.0):
        raise ValueError("H/D/A probabilities do not sum to one")
    return ordered
def main():
    data = pd.read_csv(FEATURE_PATH, parse_dates=["date"])
    # Restrict the working frame to the established train and validation seasons.
    data = data[data.season.isin(TRAIN_SEASONS + VALIDATION_SEASONS)].copy()
    train = data[data.season.isin(TRAIN_SEASONS)].copy()
    valid = data[data.season.isin(VALIDATION_SEASONS)].copy()
    if len(train) != 744 or len(valid) != 250:
        raise ValueError(f"Expected train/validation sizes 744/250; got {len(train)}/{len(valid)}")
    if set(train.match_id) & set(valid.match_id):
        raise ValueError("Train and validation match IDs overlap")
    if set(train.outcome_90m) != set(CLASS_ORDER):
        raise ValueError("Training split does not contain all H/D/A labels")
    # Stream the combined historical metric file and retain validation rows only.
    validation_rows = []
    with METRICS_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["period"] == "validation" and row["model"] in ["Baseline", "Model A", "Model B", "Model C"]:
                validation_rows.append(row)
    existing = pd.DataFrame(validation_rows)
    for column in ["n", "log_loss", "multiclass_brier", "accuracy", "precision_macro", "recall_macro", "f1_macro", "recall_H", "recall_D", "recall_A"]:
        existing[column] = pd.to_numeric(existing[column])
    if set(existing.model) != {"Baseline", "Model A", "Model B", "Model C"} or not existing.n.eq(250).all():
        raise ValueError("Saved validation metrics do not match the expected four 250-row comparisons")
    rows, confusion_rows, prediction_rows = [], [], []
    for feature_model, cols in FEATURE_SETS.items():
        estimator = make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(**RF_CONFIG),
        )
        estimator.fit(train[cols], train.outcome_90m)
        probs = ordered_probabilities(estimator, valid[cols])
        result = metric_row(f"Random Forest {feature_model[-1]}", valid.outcome_90m, probs, valid, "validation")
        result.update({"feature_set": feature_model, "n_features": len(cols)})
        rows.append(result)
        pred = np.asarray(CLASS_ORDER)[probs.argmax(axis=1)]
        matrix = confusion_matrix(valid.outcome_90m, pred, labels=CLASS_ORDER)
        for i, actual in enumerate(CLASS_ORDER):
            for j, predicted in enumerate(CLASS_ORDER):
                confusion_rows.append({"model": result["model"], "actual": actual, "predicted": predicted, "count": int(matrix[i, j])})
        for ix, row in enumerate(valid.itertuples(index=False)):
            prediction_rows.append({
                "model": result["model"], "match_id": row.match_id, "season": row.season,
                "date": row.date.date().isoformat(), "actual": row.outcome_90m,
                "predicted": pred[ix], "p_H": float(probs[ix, 0]), "p_D": float(probs[ix, 1]), "p_A": float(probs[ix, 2]),
            })
    OUT.mkdir(parents=True, exist_ok=True)
    rf_metrics = pd.DataFrame(rows)
    rf_metrics.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(confusion_rows).to_csv(OUT / "confusion_matrices.csv", index=False)
    pd.DataFrame(prediction_rows).to_csv(OUT / "predictions.csv", index=False)
    comparison = pd.concat([existing.assign(feature_set=existing.model, n_features=np.nan), rf_metrics], ignore_index=True, sort=False)
    comparison.to_csv(OUT / "comparison.csv", index=False)
    manifest = {
        "experiment": "supplementary Random Forest validation-only comparison",
        "train_seasons": TRAIN_SEASONS, "train_rows": len(train),
        "validation_seasons": VALIDATION_SEASONS, "validation_rows": len(valid),
        "target": "90-minute H/D/A", "class_order": CLASS_ORDER,
        "feature_sets": FEATURE_SETS, "random_forest": RF_CONFIG,
        "preprocessing": "Median imputer fitted inside each training-only sklearn pipeline; no scaling because tree splits are scale invariant.",
        "validation_only": True,
        "final_test_used": False,
        "selection_or_tuning": "No hyperparameter search; one predeclared configuration, with A/B/C feature variants compared on the established validation period. This supplementary experiment does not alter original selection.",
        "sources_sha256": {"historical_features.csv": sha256(FEATURE_PATH), "frozen_metrics.csv": sha256(METRICS_PATH)},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(rf_metrics[["model", "n", "log_loss", "multiclass_brier", "accuracy", "f1_macro", "recall_D"]].to_string(index=False))
    print(f"Saved supplementary results under {OUT.relative_to(ROOT)}")
if __name__ == "__main__":
    main()
