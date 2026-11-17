# Validation-only diagnosis of Model C draw probabilities

**Status:** Completed using only the 2015/16–2020/21 training rows and 2021/22–2022/23 validation rows. The final-test rows were discarded by the diagnostic script and were not scored or used to select these configurations. Earlier project work had evaluated and reported the original C=1 final-test results; this diagnosis did not use them for selection. The selected C=0.003 setting was later scored on the final period only after selection was frozen.

## Question and method

Model C previously assigned no validation/final-test match a draw as its highest-probability class. This analysis asks whether the cause appears to be class imbalance, probability calibration, feature redundancy, or model specification, and whether validation supports a different common regularization level or class weighting.

The reproducible script is src/diagnose_model_c_draws.py. It retains only training seasons 2015/16–2020/21 and validation seasons 2021/22–2022/23, checks the expected 744/250 rows and eight seasons, and writes separate validation diagnostics under data/results/validation_*. It uses the existing feature construction, class order H/D/A, train-only median imputation and scaling, and multinomial Logistic Regression. No threshold was changed.

The training set has 338 H, 159 D, and 247 A outcomes (45.4%, 21.4%, 33.2%). Validation has 117 H, 52 D, and 81 A (46.8%, 20.8%, 32.4%). This is moderate class imbalance, not an absence of draws or a very rare draw class.

## Validation comparisons

Log loss and multiclass Brier are lower-is-better. The regularization search uses one shared C across A/B/C, so feature-group comparisons remain controlled. C is the inverse regularization strength: lower C applies stronger L2 shrinkage.

| Validation specification | Log loss | Multiclass Brier | Accuracy | Predicted H / D / A | Draw recall |
|---|---:|---:|---:|---:|---:|
| Frequency baseline | 1.0475 | 0.6330 | 0.468 | 250 / 0 / 0 | 0.000 |
| Model A, C=1 | 0.9960 | 0.5862 | 0.544 | 123 / 0 / 127 | 0.000 |
| Model B, C=1 | 0.9899 | 0.5813 | 0.564 | 125 / 0 / 125 | 0.000 |
| Model C, C=1 | 0.9974 | 0.5828 | 0.564 | 127 / 0 / 123 | 0.000 |
| Model A, C=0.003 | 0.9620 | 0.5685 | 0.552 | 132 / 0 / 118 | 0.000 |
| Model B, C=0.003 | 0.9578 | 0.5661 | 0.560 | 136 / 0 / 114 | 0.000 |
| Model C, C=0.003 | 0.9491 | 0.5599 | 0.564 | 134 / 0 / 116 | 0.000 |
| Model C, C=0.003, balanced class weights | 0.9811 | 0.5824 | 0.540 | 110 / 13 / 127 | 0.058 |
| Model C + absolute raw Elo gap, C=0.003 | 0.9489 | 0.5595 | 0.568 | 135 / 0 / 115 | 0.000 |

Across the shared grid C = 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, and 10, C=0.003 gave the lowest validation log loss and Brier for each of Models A, B, and C. It improved both primary metrics over C=1 for all three variants, with only small or no accuracy gains. Model C at C=0.003 is the selected candidate because the research prioritizes probability quality and the shared setting preserves a controlled A/B/C comparison. This is selection on one 250-match validation period, so it may still be optimistic; it is not evidence of a universally optimal C.

Class weighting was considered because of the draw argmax failure. Balanced weights produce some draw argmaxes, but at C=0.003 the draw recall is only 5.8% and both primary metrics and accuracy worsen relative to the unweighted candidate. At C=1, balanced weights predict 22 draws but also worsen log loss to 1.0142 and Brier to 0.5961. This changes the marginal probability allocation and does not improve the project’s primary probabilistic objective. It is not selected.

A predeclared absolute raw-Elo-gap feature was also tested because close team strengths may be associated with draws. At C=0.003 it changes log loss by only 0.0002 and Brier by 0.0004, and still predicts no draws as the most likely outcome. Given this negligible validation difference and added complexity, it is not selected.

## Probabilities, calibration, and home/away bias

On validation, Model C at C=1 assigns mean H/D/A probabilities 0.421/0.155/0.424, while observed frequencies are 0.468/0.208/0.324. It therefore underpredicts home wins and draws and overpredicts away wins on this period. At selected C=0.003 the mean probabilities are 0.430/0.178/0.391: closer, but the same direction of misallocation remains. This is a probability-distribution bias toward away outcomes, although the argmax counts are almost balanced between H and A. It is not a simple “predict home for everything” failure. The frequency baseline predicts H for every validation row because H is its largest class prior.

For Model C at C=1, mean draw probability is 0.163 for actual draws, versus 0.144 for actual home wins and 0.165 for actual away wins. The distributions overlap substantially. With C=0.003, validation draw-probability quantile bins contain 50 matches each; observed draw frequencies are 0.14, 0.22, 0.18, 0.24, and 0.26 for mean predicted draw probabilities 0.128, 0.156, 0.176, 0.200, and 0.232. The selected candidate’s mean draw probability (0.178) remains below the 0.208 observed draw rate, but the bin-level pattern is noisy and not monotonically calibrated. A 250-match validation set is too small to make fine-grained calibration claims.

The original unweighted C=1 Model C’s no-draw-argmax pattern is also present on validation, so it is not solely a late-season/final-test artifact. However, the primary probabilistic metrics still distinguish the candidates even when argmax draw recall is zero. Do not change the class threshold just to increase draw classification.

A verified high-confidence validation error for the C=0.003 candidate is Manchester City–Sporting CP on 2022-03-09: actual D, predicted H, with probabilities 0.760/0.120/0.120. Other high-confidence validation misses are saved in validation_draw_errors.csv.

## Feature and model diagnosis

Outcome-conditioned validation summaries in data/results/validation_feature_by_outcome.csv show draws often lie between decisive outcomes on team-strength features. For example, mean home historical points per match is 1.351 for draws (1.627 for home wins, 1.244 for away wins); mean Elo difference including home advantage is +41 for draws (+113 for home wins, -6 for away wins). The recent-points difference averages -0.320 for draws, +0.254 for home wins, and -0.416 for away wins. This is consistent with draws often occurring in relatively balanced matchups, but does not establish causality.

Training-only feature correlations are high: home prior matches with home-at-home prior matches r=0.999; home points per match with home win rate r=0.970; away points per match with away win rate r=0.970; and several cumulative/recent goals and points features have absolute correlations above 0.85. Model C includes redundant summaries and derived differences. Stronger L2 regularization plausibly helps shrink redundant coefficients. The feature-correlation evidence does not prove that multicollinearity alone caused the draw issue.

The estimator is multinomial logistic regression: it models linear class log-odds from standardized features and chooses the largest class probability for the hard prediction. It has no explicit nonlinear “team strength closeness” response or match-level interactions. The absolute Elo-gap experiment did not materially improve validation probabilities or draw argmaxes. A richer nonlinear model could be explored later, but it should not precede the required simple, explainable baseline or be selected without the same chronological validation protocol.

## Decision from validation

- Select unweighted multinomial Logistic Regression with C=0.003 as the shared A/B/C candidate for the next evaluation; retain H/D/A argmax and report its draw failure honestly.
- Do not select balanced class weights, a threshold adjustment, or the absolute-Elo-gap feature from this validation analysis.
- After this validation-based selection was frozen, the existing chronological evaluator scored C=0.003 on the final period for reporting only. No model choice was changed using those scores. The original C=1 results and predictions were copied to data/results/initial_c1/ and reports/figures/initial_c1/ before the selected run.
- Keep accuracy secondary. The primary selection basis is validation log loss and Brier across all feature variants, not the count of predicted draws.
- The evaluation is a single validation window; document selection uncertainty. A future rolling-origin analysis should be planned if time permits.

## Output files

- data/results/validation_draw_diagnostics.csv
- data/results/validation_draw_confusions.csv
- data/results/validation_draw_calibration.csv
- data/results/validation_draw_probability_summary.csv
- data/results/validation_draw_errors.csv
- data/results/validation_class_balance.csv
- data/results/validation_feature_by_outcome.csv
- data/results/validation_train_feature_correlations.csv
- data/results/validation_draw_diagnostic_manifest.json

The script manifest records the training/validation seasons and rows, search specifications, and that final-test rows were not retained for diagnosis.


## Post-selection final evaluation (reporting only)

After selection was locked using the validation results above, the existing chronological evaluator was run with a common C=0.003 for Models A–C. Final-test results were: Model A log loss 0.9308 / Brier 0.5485; Model B 0.9324 / 0.5492; Model C 0.9306 / 0.5481. Accuracy was 0.5865, 0.5825, and 0.5825, respectively. The saved final-test probability rows still contain no draw argmax predictions for A, B, or C; Model C draw precision/recall/F1 are zero. Its average predicted H/D/A probabilities are 0.452/0.191/0.357, versus observed frequencies 0.499/0.173/0.328. These figures are reported, not used for another model change. Model A and C are effectively close on the primary metrics, and no uncertainty interval has been calculated.
