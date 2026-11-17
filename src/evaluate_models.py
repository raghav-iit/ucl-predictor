from __future__ import annotations

from pathlib import Path

import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURE_PATH = ROOT / "data" / "processed" / "historical_features.csv"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "results"
DEFAULT_FIGURE_PATH = ROOT / "reports" / "figures" / "calibration_test.png"
DEFAULT_LOGISTIC_C = 0.003

CLASS_ORDER = ["H", "D", "A"]
A_FEATURES = [
    "home_prior_matches", "home_points_per_match", "home_goals_for_per_match",
    "home_goals_against_per_match", "home_goal_diff_per_match", "home_win_rate",
    "home_draw_rate", "away_prior_matches", "away_points_per_match",
    "away_goals_for_per_match", "away_goals_against_per_match",
    "away_goal_diff_per_match", "away_win_rate", "away_draw_rate",
    "home_team_home_prior_matches", "home_team_home_points_per_match",
    "away_team_away_prior_matches", "away_team_away_points_per_match",
]
B_FEATURES = A_FEATURES + ["elo_difference"]
C_FEATURES = B_FEATURES + [
    "home_recent_matches", "home_recent5_points_per_match",
    "home_recent5_goal_diff_per_match", "away_recent_matches",
    "away_recent5_points_per_match", "away_recent5_goal_diff_per_match",
    "recent5_points_difference", "recent5_goal_diff_difference",
]
FEATURE_SETS = {"Model A": A_FEATURES, "Model B": B_FEATURES, "Model C": C_FEATURES}


def probabilities_for(model, X: pd.DataFrame) -> np.ndarray:
    raw = model.predict_proba(X)
    order = [list(model.classes_).index(label) for label in CLASS_ORDER]
    return raw[:, order]


def metric_row(name: str, y: pd.Series, probabilities: np.ndarray, subset: pd.DataFrame, period: str) -> dict:
    y_array = y.to_numpy()
    predictions = np.asarray(CLASS_ORDER)[probabilities.argmax(axis=1)]
    one_hot = np.column_stack([y_array == label for label in CLASS_ORDER]).astype(float)
    class_index = {label: index for index, label in enumerate(CLASS_ORDER)}
    observed_probability = probabilities[
        np.arange(len(y_array)), np.array([class_index[label] for label in y_array])
    ]
    result = {
        "period": period,
        "model": name,
        "n": len(y_array),
        "log_loss": float(-np.log(np.clip(observed_probability, 1e-15, 1.0)).mean()),
        "multiclass_brier": float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))),
        "accuracy": float(accuracy_score(y_array, predictions)),
        "precision_macro": float(precision_score(y_array, predictions, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_array, predictions, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_array, predictions, labels=CLASS_ORDER, average="macro", zero_division=0)),
    }
    matrix = confusion_matrix(y_array, predictions, labels=CLASS_ORDER)
    for index, label in enumerate(CLASS_ORDER):
        true_positive = matrix[index, index]
        precision_denominator = matrix[:, index].sum()
        recall_denominator = matrix[index, :].sum()
        precision = true_positive / precision_denominator if precision_denominator else 0.0
        recall = true_positive / recall_denominator if recall_denominator else 0.0
        result[f"precision_{label}"] = float(precision)
        result[f"recall_{label}"] = float(recall)
        result[f"f1_{label}"] = float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return result


def class_priors(y: pd.Series) -> np.ndarray:
    return y.value_counts(normalize=True).reindex(CLASS_ORDER, fill_value=0).to_numpy(dtype=float)


def make_estimator(logistic_c: float):
    """Build the exact preprocessing/classifier pipeline used by evaluation."""
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=logistic_c, max_iter=2000, solver="lbfgs", random_state=335),
    )


def fit_predictions(train: pd.DataFrame, score: pd.DataFrame, features: list[str], logistic_c: float) -> np.ndarray:
    model = make_estimator(logistic_c)
    model.fit(train[features], train.outcome_90m)
    return probabilities_for(model, score[features])


def calibration_rows(model_name: str, y: pd.Series, probabilities: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    for j, label in enumerate(CLASS_ORDER):
        frame = pd.DataFrame({"probability": probabilities[:, j], "observed": (y.to_numpy() == label).astype(int)})
        if frame.probability.nunique() == 1:
            grouped = [("constant", frame)]
        else:
            try:
                frame["bin"] = pd.qcut(frame.probability, q=5, duplicates="drop")
            except ValueError:
                continue
            grouped = list(frame.groupby("bin", observed=True))
        for bin_number, (interval, group) in enumerate(grouped):
            rows.append({
                "model": model_name,
                "class": label,
                "bin_number": bin_number,
                "bin": str(interval),
                "n": len(group),
                "mean_predicted_probability": group.probability.mean(),
                "observed_frequency": group.observed.mean(),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the chronological UCL outcome models.")
    parser.add_argument("--logistic-c", type=float, default=DEFAULT_LOGISTIC_C)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-path", type=Path, default=DEFAULT_FIGURE_PATH)
    args = parser.parse_args()
    if args.logistic_c <= 0:
        parser.error("--logistic-c must be positive")
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    figure_path = args.figure_path if args.figure_path.is_absolute() else ROOT / args.figure_path
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(FEATURE_PATH, parse_dates=["date"])
    validation_train = data[data.season <= "2020-21"].copy()
    validation = data[data.season.isin(["2021-22", "2022-23"])].copy()
    final_train = data[data.season <= "2022-23"].copy()
    final_test = data[data.season.isin(["2023-24", "2024-25", "2025-26"])].copy()

    splits = [
        ("validation", validation_train, validation),
        ("final_test", final_train, final_test),
    ]
    split_manifest = data[["match_id", "season", "date"]].copy()
    split_manifest["validation_assignment"] = np.select(
        [split_manifest.season <= "2020-21", split_manifest.season.isin(["2021-22", "2022-23"])],
        ["train", "validation"], default="not_used_in_validation",
    )
    split_manifest["final_assignment"] = np.where(
        split_manifest.season <= "2022-23", "train", "test",
    )
    metadata_dir = ROOT / "data" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    split_manifest.to_csv(metadata_dir / "evaluation_split_assignments.csv", index=False)
    metric_rows: list[dict] = []
    confusion_rows: list[dict] = []
    prediction_rows: list[dict] = []
    calibration: list[dict] = []

    for period, train, score in splits:
        if train.empty or score.empty:
            raise ValueError(f"Empty chronological split: {period}")
        prior = class_priors(train.outcome_90m)
        baseline = np.tile(prior, (len(score), 1))
        model_probabilities: dict[str, np.ndarray] = {"Baseline": baseline}
        for name, features in FEATURE_SETS.items():
            model_probabilities[name] = fit_predictions(train, score, features, args.logistic_c)

        for name, probs in model_probabilities.items():
            overall_metric = metric_row(name, score.outcome_90m, probs, score, period)
            overall_metric.update({"format_era": None, "competition_phase": None})
            metric_rows.append(overall_metric)
            pred = np.asarray(CLASS_ORDER)[probs.argmax(axis=1)]
            matrix = confusion_matrix(score.outcome_90m, pred, labels=CLASS_ORDER)
            for i, actual in enumerate(CLASS_ORDER):
                for j, predicted in enumerate(CLASS_ORDER):
                    confusion_rows.append({
                        "period": period, "model": name, "actual": actual,
                        "predicted": predicted, "count": int(matrix[i, j]),
                    })
            for index, (_, row) in enumerate(score.iterrows()):
                record = {
                    "period": period, "model": name, "match_id": row.match_id,
                    "season": row.season, "date": row.date.date().isoformat(),
                    "competition_phase": row.competition_phase,
                    "format_era": row.format_era, "actual": row.outcome_90m,
                    "predicted": pred[index],
                }
                record.update({f"p_{label}": float(probs[index, j]) for j, label in enumerate(CLASS_ORDER)})
                prediction_rows.append(record)
            if period == "final_test":
                calibration.extend(calibration_rows(name, score.outcome_90m, probs))

                for phase, phase_rows in score.groupby(["format_era", "competition_phase"]):
                    idx = score.index.get_indexer(phase_rows.index)
                    phase_probs = probs[idx]
                    phase_metric = metric_row(name, phase_rows.outcome_90m, phase_probs, phase_rows, period)
                    phase_metric["format_era"], phase_metric["competition_phase"] = phase
                    metric_rows.append(phase_metric)

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    pd.DataFrame(confusion_rows).to_csv(output_dir / "confusion_matrices.csv", index=False)
    pd.DataFrame(prediction_rows).to_csv(output_dir / "predictions.csv", index=False)
    calibration_frame = pd.DataFrame(calibration)
    calibration_frame.to_csv(output_dir / "calibration_bins.csv", index=False)
    if not calibration_frame.empty:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharex=True, sharey=True)
        for ax, label in zip(axes, CLASS_ORDER):
            for name in ["Baseline", "Model A", "Model B", "Model C"]:
                subset = calibration_frame[
                    calibration_frame.model.eq(name) & calibration_frame["class"].eq(label)
                ].sort_values("bin_number")
                if not subset.empty:
                    ax.plot(
                        subset.mean_predicted_probability,
                        subset.observed_frequency,
                        marker="o",
                        label=name,
                    )
            ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
            ax.set(title=f"{label} class", xlabel="Mean predicted probability", xlim=(0, 1), ylim=(0, 1))
        axes[0].set_ylabel("Observed frequency")
        axes[-1].legend(loc="best", fontsize="small")
        fig.suptitle("Final-test calibration by class")
        fig.tight_layout()
        fig.savefig(figure_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
    config = {
        "logistic_c": args.logistic_c,
        "solver": "lbfgs",
        "max_iter": 2000,
        "random_state": 335,
        "class_order": CLASS_ORDER,
        "imputation": "median; fitted within training-only pipeline",
        "scaling": "StandardScaler; fitted within training-only pipeline",
        "feature_sets": FEATURE_SETS,
        "validation_train_seasons": sorted(validation_train.season.unique().tolist()),
        "validation_seasons": sorted(validation.season.unique().tolist()),
        "validation_train_rows": len(validation_train),
        "validation_rows": len(validation),
        "final_train_seasons": sorted(final_train.season.unique().tolist()),
        "final_test_seasons": sorted(final_test.season.unique().tolist()),
        "final_train_rows": len(final_train),
        "final_test_rows": len(final_test),
        "primary_metrics": ["log_loss", "multiclass_brier"],
        "split_assignments_file": "data/metadata/evaluation_split_assignments.csv",
    }
    (output_dir / "model_config.json").write_text(json.dumps(config, indent=2) + "\n")
    print("Logistic regression C:", args.logistic_c)
    print("Saved evaluation outputs to:", output_dir)
    print("Validation split:", len(validation_train), "train /", len(validation), "validation matches")
    print("Final split:", len(final_train), "train /", len(final_test), "test matches")
    print(metrics[metrics.competition_phase.isna()][["period", "model", "n", "log_loss", "multiclass_brier", "accuracy", "f1_macro"]].to_string(index=False))
    print("Final test phase sample sizes:")
    print(final_test.groupby(["format_era", "competition_phase"]).size().to_string())


if __name__ == "__main__":
    main()

