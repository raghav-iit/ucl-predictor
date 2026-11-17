# Model results

**Current selected configuration:** multinomial Logistic Regression with median imputation and standard scaling, both fitted on training rows only. A common C=0.003 is used across Models A–C. This setting was selected using only the chronological validation period. The earlier C=1 run is preserved in data/results/initial_c1/ and reports/figures/initial_c1/ for transparency.

The selected configuration was evaluated on the existing final period after model selection. The original C=1 final-test results had already been reported in prior project work; the final period was not used in the new C selection or alternative-specification search.

## Primary and secondary metrics

Log loss penalizes low probability assigned to the observed class, with especially large penalties for confident mistakes. Multiclass Brier score is the per-match sum of squared errors across H/D/A probabilities, averaged over matches; lower is better. Accuracy only checks the top-probability class, so it is secondary for this probabilistic question.

| Period | Model | n | Log loss | Multiclass Brier | Accuracy | Macro F1 |
|---|---|---:|---:|---:|---:|---:|
| Validation | Frequency baseline | 250 | 1.0475 | 0.6330 | 0.4680 | 0.2125 |
| Validation | Model A | 250 | 0.9620 | 0.5685 | 0.5520 | 0.4072 |
| Validation | Model B | 250 | 0.9578 | 0.5661 | 0.5600 | 0.4128 |
| Validation | Model C | 250 | 0.9491 | 0.5599 | 0.5640 | 0.4153 |
| Final test | Frequency baseline | 503 | 1.0217 | 0.6167 | 0.4990 | 0.2219 |
| Final test | Model A | 503 | 0.9308 | 0.5485 | 0.5865 | 0.4224 |
| Final test | Model B | 503 | 0.9324 | 0.5492 | 0.5825 | 0.4199 |
| Final test | Model C | 503 | 0.9306 | 0.5481 | 0.5825 | 0.4198 |

Model A improves substantially over the frequency baseline on both primary test metrics. On the final test, adding Elo (B) slightly worsens log loss and Brier relative to A. Adding recent form (C) recovers a very small improvement relative to B; C is nearly tied with A on both primary scores. Accuracy is highest for A. These small differences do not establish a robust Elo or recent-form gain, especially without uncertainty intervals.

The lower C was selected because the same validation grid favored C=0.003 for A, B and C on both primary metrics. It also changed the final-test results. Model C C=1 previously had final-test log loss 0.9546 and Brier 0.5590; the selected C=0.003 run has 0.9306 and 0.5481. The earlier results remain in the initial_c1 archive. Because the old test metrics had been seen before this change, interpret this updated test comparison cautiously: the new setting was chosen on validation, but this is not a pristine test set in the strict historical sense.

## Original C=1 results retained

| Period | Model | n | Log loss | Multiclass Brier | Accuracy |
|---|---|---:|---:|---:|---:|
| Validation | Model A | 250 | 0.9960 | 0.5862 | 0.5440 |
| Validation | Model B | 250 | 0.9899 | 0.5813 | 0.5640 |
| Validation | Model C | 250 | 0.9974 | 0.5828 | 0.5640 |
| Final test | Model A | 503 | 0.9664 | 0.5657 | 0.5865 |
| Final test | Model B | 503 | 0.9616 | 0.5613 | 0.5924 |
| Final test | Model C | 503 | 0.9546 | 0.5590 | 0.5944 |

The original C=1 run is a historical configuration, not the selected model. Its outputs are preserved under data/results/initial_c1/.

## Supplementary Random Forest validation experiment

A separate one-configuration Random Forest comparison was performed on the established 744/250 train-validation split, with matched A/B/C feature groups and no final-test use. Random Forest A had a slightly higher macro F1 and found one validation draw, but Model C retained lower log loss and multiclass Brier; no Random Forest variant established an overall improvement. This exploratory comparison does not change the selected Logistic Regression configuration or original saved evaluation. See [random_forest_validation_experiment.md](random_forest_validation_experiment.md) for configuration, all metrics and confusion matrices. The final-test metrics had been inspected in earlier work and were not used in this RF experiment.

## Selected-model draw failure and error analysis

The selected unweighted Models A–C still predict no draws as the highest-probability class on the final test. There are 87 actual draws; draw precision, recall and F1 are all zero for each model. Model C's selected-test predicted class counts are H=287, D=0, A=216, while actual counts are H=251, D=87, A=165. Its mean predicted probabilities are H=0.452, D=0.191, A=0.357, compared with observed frequencies H=0.499, D=0.173, A=0.328. Average draw probability is not absent, but it never becomes the maximum class probability.

Representative Model C final-test errors:

| Match | Actual regulation score / result | Predicted H/D/A probabilities | Error |
|---|---|---|---|
| Bayern Munich–Celtic, 2025-02-18 | 1–1, draw | 0.841 / 0.096 / 0.062 | High-confidence home-win prediction |
| Manchester City–Feyenoord, 2024-11-26 | 3–3, draw | 0.836 / 0.104 / 0.060 | High-confidence home-win prediction |
| Bayern Munich–Copenhagen, 2023-11-29 | 0–0, draw | 0.827 / 0.105 / 0.068 | High-confidence home-win prediction |
| Real Madrid–AC Milan, 2024-11-05 | 1–3, away win | 0.800 / 0.113 / 0.087 | Confidently predicts home win |

These examples show the difference between probabilistic scoring and the argmax class prediction, but also expose serious overconfidence on some errors. The calibration figure and bins should be read alongside these examples, not as proof that calibration is adequate. Validation diagnostics and the model-selection decision are documented in docs/model_c_draw_diagnosis.md.

## Selected-model phase results

| Format era / phase | n | Model A log loss / Brier | Model B log loss / Brier | Model C log loss / Brier |
|---|---:|---:|---:|---:|
| 32-team group-stage era / group phase | 96 | 0.8971 / 0.5221 | 0.8880 / 0.5159 | 0.8975 / 0.5233 |
| 32-team group-stage era / knockout | 29 | 0.9845 / 0.5778 | 0.9869 / 0.5809 | 0.9983 / 0.5886 |
| 36-team league-phase era / league phase | 288 | 0.9195 / 0.5414 | 0.9245 / 0.5440 | 0.9175 / 0.5392 |
| 36-team league-phase era / knockout playoff | 32 | 1.0169 / 0.6106 | 1.0262 / 0.6170 | 1.0155 / 0.6112 |
| 36-team league-phase era / other knockout | 58 | 0.9684 / 0.5787 | 0.9663 / 0.5764 | 0.9691 / 0.5780 |

Knockout and playoff subsets are small, particularly n=29 and n=32. These descriptive slices cannot establish that one phase is more predictable than another. The old group format and new league phase also differ in teams, opponent mix, and schedule structure.

## Calibration and saved outputs

The final-test one-vs-rest reliability plot is reports/figures/calibration_test.png; its bins are data/results/calibration_bins.csv. Match probabilities, confusion matrices, and metrics are saved in data/results/predictions.csv, data/results/confusion_matrices.csv, and data/results/metrics.csv. The frozen estimator and split settings are in data/results/model_config.json. Reproduce the current run with:

.venv/bin/python src/evaluate_models.py --logistic-c 0.003
.venv/bin/streamlit run app.py

The final-training estimator pipelines used for manual future-fixture inference are separate artifacts under `data/models/`, with their fit boundary and hashes in `prediction_model_manifest.json`. They are fitted on the same 994-row final-training block and reproduce the saved final-test probabilities exactly; they are not new test results and do not change the reported evaluation files. The future-feature state snapshot is `data/processed/team_state_snapshot.json`.

To reproduce the original historical C=1 run in a separate folder, use:

.venv/bin/python src/evaluate_models.py --logistic-c 1.0 --output-dir data/results/initial_c1 --figure-path reports/figures/initial_c1/calibration_test.png

## Limitations

- The draw argmax failure and overconfident missed draws remain unresolved. Class weighting produced some draw predictions on validation but worsened log loss and Brier; it was not selected.
- No uncertainty intervals have yet been estimated. Match predictions share teams/seasons, so independent-row intervals may understate uncertainty.
- One 250-match validation window selected C. The grid search can still overfit that period; C=0.003 is a selected setting, not a proven optimum.
- Regularized multinomial logistic regression is one linear additive model family. No claim is made that it is the best possible estimator.
- Team aliases are project-derived rather than official IDs. Source counts agree with OpenFootball headers, but an independent match-by-match official audit is incomplete.
- The final period crosses the 2024/25 format change. Phase results are exploratory.
- FIFA/SoFIFA data was investigated but excluded from all evaluated models. The annual FIFA 15–23 data has one snapshot per edition, the 5.6 GB all-updates file was not downloaded/audited, later one-off snapshots do not provide a consistent time-safe panel, snapshot club membership is not UCL registration, and historical starting lineups are not available in the match table. Model D has no results; see docs/sofifa_research.md.
- 2026/27 results and an automated upcoming-fixture feed are not implemented. The historical explorer reports saved retrospective predictions; the separate manual fixture form produces estimates without validating an official fixture or using live current-season data.
