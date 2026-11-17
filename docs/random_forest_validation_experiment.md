# Supplementary Random Forest validation experiment

**Status:** exploratory validation-only comparison. This is separate from the project's frozen Baseline/Models A–C evaluation and does not change their selected configuration, saved predictions, metrics, or final-training inference pipelines.

## Question and design

Does one fixed Random Forest specification improve validation prediction over the existing frequency baseline and regularized Logistic Regression Models A–C, using the existing A/B/C feature groups?

The experiment uses only the established chronological split:

- Training: 2015/16–2020/21, 744 matches.
- Validation: 2021/22–2022/23, 250 matches.
- The three RF feature variants use the same ordered A/B/C columns as the original evaluation.
- No final-test labels, predictions, or metrics are used by the experiment script. The project's final-test results had been inspected in earlier work, so they should not be described as a completely untouched holdout.

The single predeclared Random Forest configuration is 500 trees, `max_features="sqrt"`, `min_samples_leaf=5`, unrestricted depth, no class weighting, and random seed 335. A median `SimpleImputer` is fit inside each training-only scikit-learn pipeline. Scaling is omitted because tree split rules do not require standardized feature scales. No hyperparameter search or calibration was performed. RF A, B and C differ only in feature columns.

The scorer reorders `predict_proba()` columns by the fitted classifier's `classes_` into the fixed H/D/A order before computing metrics. This prevents reliance on an implicit class order. The primary metrics and multiclass Brier-score formula match `src/evaluate_models.py`.

## Validation results

All rows below are the same 250 validation matches. Lower is better for log loss and Brier; higher is better for the remaining metrics.

| Model | Feature set | Log loss | Multiclass Brier | Accuracy | Macro F1 | Draw recall |
|---|---|---:|---:|---:|---:|---:|
| Baseline | Training outcome frequencies | 1.0475 | 0.6330 | 0.4680 | 0.2125 | 0.0000 |
| Model A | Historical team performance | 0.9620 | 0.5685 | 0.5520 | 0.4071 | 0.0000 |
| Model B | A + Elo difference | 0.9578 | 0.5661 | 0.5600 | 0.4128 | 0.0000 |
| Model C | B + recent form | **0.9491** | **0.5599** | **0.5640** | 0.4153 | 0.0000 |
| Random Forest A | A features | 0.9525 | 0.5637 | 0.5520 | **0.4204** | 0.0192 |
| Random Forest B | B features | 0.9534 | 0.5647 | 0.5520 | 0.4099 | 0.0000 |
| Random Forest C | C features | 0.9574 | 0.5667 | 0.5440 | 0.4152 | 0.0192 |

RF A has the strongest macro F1 among these rows and predicts one of the 52 actual draws correctly (draw recall 1/52). It does not improve accuracy over Model C, and its log loss and Brier score are worse than Model C by 0.0034 and 0.0038 respectively. RF B and RF C also do not beat Model C on either primary metric. The very small draw-recall gains represent one correctly predicted draw, not evidence of a reliable solution to draw prediction.

**Decision:** retain the existing Baseline and Models A–C as the project models. This one-shot experiment does not demonstrate an across-metric improvement that justifies replacing or adding a selected model. It does not modify the original model-selection decision.

## Confusion matrices

Rows are actual classes H, D, A; columns are predicted classes H, D, A. Each cell is the match count.

| Model | Confusion matrix (H row; D row; A row) |
|---|---|
| Baseline | 117, 0, 0; 52, 0, 0; 81, 0, 0 |
| Model A | 82, 0, 35; 25, 0, 27; 25, 0, 56 |
| Model B | 84, 0, 33; 27, 0, 25; 25, 0, 56 |
| Model C | 85, 0, 32; 24, 0, 28; 25, 0, 56 |
| Random Forest A | 79, 1, 37; 27, 1, 24; 22, 1, 58 |
| Random Forest B | 81, 1, 35; 29, 0, 23; 23, 1, 57 |
| Random Forest C | 78, 2, 37; 28, 1, 23; 23, 1, 57 |

The forest models reduce the all-home argmax behavior of the frequency baseline, but still miss 51/52 validation draws in the A and C variants and all 52 in B. All three logistic models also miss all 52 as argmax outcomes. Probabilities can assign non-zero mass to draws even when D is not the most probable class; draw recall here measures only the argmax classification.

## Interpretation and limitations

- This is one fixed RF configuration, not a tuned Random Forest study. Its parameter values were set before the run; there was no validation search over tree count, depth, leaf size, or class weighting.
- The 250-match validation period was already used to select the original Logistic Regression C. Reusing it for this additional comparison makes the result exploratory and may overstate performance. The experiment did not inspect or use the final-test period.
- Seven model rows are compared on one validation sample. Tiny score differences are not evidence of statistically reliable gains; no uncertainty intervals or paired significance tests were computed.
- The Random Forest's probability estimates were not recalibrated. Log loss and Brier score are therefore important to inspect alongside the argmax metrics, and a modest macro-F1 increase alone is insufficient to claim better probabilistic forecasting.
- The dataset is small for a flexible tree ensemble (744 training rows), class-imbalanced, and consists of repeated clubs and seasons. The fixed forest may still overfit interactions.
- Median imputation is fit on training rows only. Missing values and feature timing remain governed by the existing feature table. Features are start-of-day state for each date, with that date's match outcomes applied only after all same-day feature rows are constructed.
- Model D/player ratings, current-season data and tournament advancement are outside this experiment.

## Reproduction and artifacts

Run from the project root:

```bash
.venv/bin/python src/evaluate_random_forest_validation.py
```

The script asserts the 744/250 split and writes only to `reports/random_forest_validation/`:

- `metrics.csv`
- `confusion_matrices.csv`
- `predictions.csv`
- `comparison.csv`
- `manifest.json` (configuration and source SHA-256 hashes)

It does not load the prediction table, fit any original model, or write to `data/results/`. The original saved validation and final-test files remain the source of the A/B/C comparisons. scikit-learn's API documents the Random Forest configuration and probability output; the official documentation describes its tree averaging and the role of `min_samples_leaf` ([RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [SimpleImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html)).
