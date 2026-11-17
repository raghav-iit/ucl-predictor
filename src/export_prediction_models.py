"""Fit and persist inference pipelines using the frozen final-training period.

This export does not choose features or hyperparameters and never fits on the
final-test seasons. It is separate from the evaluator's reporting artifacts.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import joblib
import pandas as pd
import sklearn

from evaluate_models import DEFAULT_LOGISTIC_C, FEATURE_SETS, make_estimator

ROOT = Path(__file__).resolve().parents[1]
FEATURE_PATH = ROOT / "data" / "processed" / "historical_features.csv"
STATE_PATH = ROOT / "data" / "processed" / "team_state_snapshot.json"
MODEL_DIR = ROOT / "data" / "models"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not FEATURE_PATH.exists() or not STATE_PATH.exists():
        raise FileNotFoundError(
            "Run src/build_features.py first to create historical features and the state snapshot."
        )
    data = pd.read_csv(FEATURE_PATH)
    snapshot = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    train = data[data.season <= "2022-23"].copy()
    test = data[data.season.isin(["2023-24", "2024-25", "2025-26"])]
    if len(train) != 994 or len(test) != 503:
        raise ValueError(f"Unexpected frozen split sizes: train={len(train)}, test={len(test)}")
    if snapshot.get("as_of_date") != data.date.max():
        raise ValueError("Team-state snapshot date does not match the latest processed feature date")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    saved = {}
    for name, features in FEATURE_SETS.items():
        estimator = make_estimator(DEFAULT_LOGISTIC_C)
        estimator.fit(train[features], train.outcome_90m)
        if set(estimator.classes_) != {"H", "D", "A"}:
            raise ValueError(f"Unexpected fitted classes for {name}: {estimator.classes_}")
        filename = name.lower().replace(" ", "_") + ".joblib"
        path = MODEL_DIR / filename
        joblib.dump(estimator, path)
        saved[name] = {
            "path": f"data/models/{filename}",
            "sha256": sha256(path),
            "features": features,
        }

    manifest = {
        "artifact_purpose": "manual-fixture probability inference; not a new evaluation result",
        "training_rows": len(train),
        "training_seasons": sorted(train.season.unique().tolist()),
        "training_cutoff_season": "2022-23",
        "final_test_rows_used_for_estimator_fit": 0,
        "selected_logistic_c": DEFAULT_LOGISTIC_C,
        "selected_on": "the existing validation-only model-selection record",
        "solver": "lbfgs",
        "max_iter": 2000,
        "random_state": 335,
        "class_order": ["H", "D", "A"],
        "preprocessing": "median imputation and StandardScaler inside the fitted scikit-learn Pipeline",
        "historical_state_as_of_date": snapshot["as_of_date"],
        "state_snapshot_path": "data/processed/team_state_snapshot.json",
        "state_snapshot_sha256": sha256(STATE_PATH),
        "feature_table_sha256": sha256(FEATURE_PATH),
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "models": saved,
        "method_note": (
            "The pipelines are refit on the frozen final-training seasons only. The separate latest-state "
            "snapshot includes results through its stated date because those results precede any requested "
            "future prediction date. Do not present predictions from these assets as test metrics."
        ),
    }
    (MODEL_DIR / "prediction_model_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved A/B/C inference pipelines to {MODEL_DIR}")
    print(f"Fit rows: {len(train)} through season 2022-23; final-test fit rows: 0")
    print(f"Prediction-time team state is available through {snapshot['as_of_date']}")


if __name__ == "__main__":
    main()
