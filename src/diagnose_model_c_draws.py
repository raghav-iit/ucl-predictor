from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evaluate_models import A_FEATURES, B_FEATURES, C_FEATURES, CLASS_ORDER, class_priors  # noqa: E402

FEATURE_PATH = ROOT / "data" / "processed" / "historical_features.csv"
OUT = ROOT / "data" / "results"
CLASS_INDEX = {label: i for i, label in enumerate(CLASS_ORDER)}
SEASONS_TRAIN = ["2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21"]
SEASONS_VALID = ["2021-22", "2022-23"]


def probabilities(model, frame, features):
    raw = model.predict_proba(frame[features])
    return raw[:, [list(model.classes_).index(c) for c in CLASS_ORDER]]


def evaluate(name, y, probs):
    y = y.to_numpy()
    pred = np.asarray(CLASS_ORDER)[probs.argmax(axis=1)]
    one_hot = np.column_stack([y == label for label in CLASS_ORDER]).astype(float)
    observed = probs[np.arange(len(y)), [CLASS_INDEX[v] for v in y]]
    cm = confusion_matrix(y, pred, labels=CLASS_ORDER)
    row = {
        "model_spec": name,
        "n": len(y),
        "log_loss": float(-np.log(np.clip(observed, 1e-15, 1)).mean()),
        "multiclass_brier": float(np.mean(np.sum((probs - one_hot) ** 2, axis=1))),
        "accuracy": float(np.mean(pred == y)),
    }
    for i, label in enumerate(CLASS_ORDER):
        tp = cm[i, i]
        precision = tp / cm[:, i].sum() if cm[:, i].sum() else 0.0
        recall = tp / cm[i, :].sum() if cm[i, :].sum() else 0.0
        row[f"actual_{label}"] = int(cm[i, :].sum())
        row[f"predicted_{label}"] = int(cm[:, i].sum())
        row[f"precision_{label}"] = float(precision)
        row[f"recall_{label}"] = float(recall)
        row[f"f1_{label}"] = float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        row[f"mean_p_{label}"] = float(probs[:, i].mean())
    return row, pred, cm


def calibration_rows(name, y, probs):
    rows = []
    for j, label in enumerate(CLASS_ORDER):
        frame = pd.DataFrame({"p": probs[:, j], "observed": (y.to_numpy() == label).astype(int)})
        if frame.p.nunique() <= 1:
            bins = [("constant", frame)]
        else:
            frame["bin"] = pd.qcut(frame.p, q=5, duplicates="drop")
            bins = list(frame.groupby("bin", observed=True))
        for bin_id, (interval, group) in enumerate(bins):
            rows.append({
                "model_spec": name, "probability_class": label, "bin_id": bin_id,
                "bin": str(interval), "n": len(group),
                "mean_predicted_probability": float(group.p.mean()),
                "observed_frequency": float(group.observed.mean()),
            })
    return rows


def main():
    # Retain only training and validation seasons before modeling. Final-test
    # season rows are discarded as they are read; no test labels/features are used.
    allowed = set(SEASONS_TRAIN + SEASONS_VALID)
    selected = []
    with FEATURE_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["season"] in allowed:
                selected.append(row)
    data = pd.DataFrame(selected)
    if data.empty:
        raise ValueError("No training/validation rows were selected")
    data["date"] = pd.to_datetime(data["date"])
    for feature in set(A_FEATURES + B_FEATURES + C_FEATURES):
        data[feature] = pd.to_numeric(data[feature], errors="coerce")
    data["elo_strength_gap_abs"] = (data["elo_difference"] - 60.0).abs()
    train = data[data.season.isin(SEASONS_TRAIN)].copy()
    valid = data[data.season.isin(SEASONS_VALID)].copy()
    if len(train) != 744 or len(valid) != 250 or data.season.nunique() != 8:
        raise ValueError("Unexpected chronological training/validation assignments")
    if data.date.max() != valid.date.max():
        raise ValueError("Selected rows extend past the validation cutoff")

    y_train, y_valid = train.outcome_90m, valid.outcome_90m
    rows, confusions, calibration, prob_summary, errors = [], [], [], [], []
    pred_sets = {}

    baseline = np.tile(class_priors(y_train), (len(valid), 1))
    spec_predictions = [("Baseline", None, None, baseline)]
    for label, features in [("Model A", A_FEATURES), ("Model B", B_FEATURES), ("Model C", C_FEATURES)]:
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=335),
        )
        model.fit(train[features], y_train)
        spec_predictions.append((label, features, None, probabilities(model, valid, features)))

    for label, features in [("Model A", A_FEATURES), ("Model B", B_FEATURES), ("Model C", C_FEATURES)]:
        for c_value in [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]:
            model = make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                LogisticRegression(C=c_value, max_iter=2000, solver="lbfgs", random_state=335),
            )
            model.fit(train[features], y_train)
            spec_predictions.append((
                f"{label} | C={c_value:g}", features, {"C": c_value},
                probabilities(model, valid, features),
            ))

    # A match-up strength-gap feature is a predeclared alternative: draws may
    # depend on closeness of underlying team strength, not just signed home edge.
    gap_features = C_FEATURES + ["elo_strength_gap_abs"]
    for c_value in [0.003, 0.01, 0.1, 1.0]:
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(C=c_value, max_iter=2000, solver="lbfgs", random_state=335),
        )
        model.fit(train[gap_features], y_train)
        spec_predictions.append((
            f"Model C + abs Elo gap | C={c_value:g}", gap_features, {"C": c_value},
            probabilities(model, valid, gap_features),
        ))

    for c_value in [0.003, 0.01, 1.0]:
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(C=c_value, max_iter=2000, solver="lbfgs", random_state=335, class_weight="balanced"),
        )
        model.fit(train[C_FEATURES], y_train)
        spec_predictions.append((
            f"Model C | balanced | C={c_value:g}", C_FEATURES,
            {"C": c_value, "class_weight": "balanced"}, probabilities(model, valid, C_FEATURES),
        ))

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=335, class_weight="balanced"),
    )
    model.fit(train[C_FEATURES], y_train)
    spec_predictions.append(("Model C | balanced weights", C_FEATURES, {"C": 1.0, "class_weight": "balanced"}, probabilities(model, valid, C_FEATURES)))

    for name, features, config, probs in spec_predictions:
        metric, pred, cm = evaluate(name, y_valid, probs)
        rows.append(metric)
        pred_sets[name] = probs
        for i, actual in enumerate(CLASS_ORDER):
            for j, predicted in enumerate(CLASS_ORDER):
                confusions.append({"model_spec": name, "actual": actual, "predicted": predicted, "count": int(cm[i, j])})
        calibration.extend(calibration_rows(name, y_valid, probs))
        for j, label in enumerate(CLASS_ORDER):
            col = probs[:, j]
            for actual in CLASS_ORDER + ["ALL"]:
                mask = np.ones(len(y_valid), dtype=bool) if actual == "ALL" else y_valid.to_numpy() == actual
                values = col[mask]
                prob_summary.append({
                    "model_spec": name, "probability_class": label, "actual_class": actual,
                    "n": len(values), "mean": float(values.mean()), "median": float(np.median(values)),
                    "q90": float(np.quantile(values, .9)), "min": float(values.min()), "max": float(values.max()),
                })
        wrong = np.flatnonzero(pred != y_valid.to_numpy())
        for idx in wrong:
            errors.append({
                "model_spec": name, "match_id": valid.iloc[idx].match_id, "date": valid.iloc[idx].date.date().isoformat(),
                "season": valid.iloc[idx].season, "home_team": valid.iloc[idx].home_team, "away_team": valid.iloc[idx].away_team,
                "actual": y_valid.iloc[idx], "predicted": pred[idx],
                "p_H": float(probs[idx, 0]), "p_D": float(probs[idx, 1]), "p_A": float(probs[idx, 2]),
                "max_probability": float(probs[idx].max()),
            })

    # Class frequencies and feature distributions are described for training and
    # validation only. Validation summaries are diagnostic, not a test set.
    class_rows = []
    for split_name, frame in [("train", train), ("validation", valid)]:
        counts = frame.outcome_90m.value_counts().reindex(CLASS_ORDER, fill_value=0)
        for label in CLASS_ORDER:
            class_rows.append({"split": split_name, "class": label, "n": int(counts[label]), "share": float(counts[label] / len(frame))})
    feature_rows = []
    for split_name, frame in [("train", train), ("validation", valid)]:
        for feature in C_FEATURES:
            for label, group in frame.groupby("outcome_90m"):
                vals = group[feature]
                feature_rows.append({
                    "split": split_name, "feature": feature, "actual": label, "n": len(group),
                    "missing_share": float(vals.isna().mean()), "mean": float(vals.mean()),
                    "median": float(vals.median()), "std": float(vals.std(ddof=1)) if vals.notna().sum() > 1 else float("nan"),
                })

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "validation_draw_diagnostics.csv", index=False)
    pd.DataFrame(confusions).to_csv(OUT / "validation_draw_confusions.csv", index=False)
    pd.DataFrame(calibration).to_csv(OUT / "validation_draw_calibration.csv", index=False)
    pd.DataFrame(prob_summary).to_csv(OUT / "validation_draw_probability_summary.csv", index=False)
    pd.DataFrame(errors).to_csv(OUT / "validation_draw_errors.csv", index=False)
    pd.DataFrame(class_rows).to_csv(OUT / "validation_class_balance.csv", index=False)
    pd.DataFrame(feature_rows).to_csv(OUT / "validation_feature_by_outcome.csv", index=False)
    corr = train[C_FEATURES].corr().abs()
    corr_pairs = []
    for i, left in enumerate(C_FEATURES):
        for right in C_FEATURES[i + 1:]:
            value = corr.loc[left, right]
            if pd.notna(value) and value >= 0.70:
                corr_pairs.append({"feature_1": left, "feature_2": right, "abs_pearson_r": float(value)})
    pd.DataFrame(corr_pairs).sort_values("abs_pearson_r", ascending=False).to_csv(
        OUT / "validation_train_feature_correlations.csv", index=False
    )
    manifest = {
        "training_seasons": SEASONS_TRAIN, "training_rows": len(train),
        "validation_seasons": SEASONS_VALID, "validation_rows": len(valid),
        "loaded_rows": len(data), "last_loaded_date": data.date.max().date().isoformat(),
        "final_test_rows_retained": False, "model_selection_uses_final_test": False,
        "specifications": ["Baseline", "Model A/B/C, C=1, unweighted", "A/B/C common C grid 0.001/0.003/0.01/0.03/0.1/0.3/1/3/10", "C plus absolute raw Elo gap at C=0.003/0.01/0.1/1", "Model C balanced weights at C=0.003/0.01/1"],
    }
    (OUT / "validation_draw_diagnostic_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(pd.DataFrame(rows)[[
        "model_spec", "log_loss", "multiclass_brier", "accuracy",
        "predicted_H", "predicted_D", "predicted_A", "recall_D", "mean_p_D",
    ]].to_string(index=False))
    print("\nClass balance:")
    print(pd.DataFrame(class_rows).pivot(index="split", columns="class", values="share").to_string())
    print("\nWrote validation-only diagnostic outputs. Final-test rows were discarded and not used.")


if __name__ == "__main__":
    main()
