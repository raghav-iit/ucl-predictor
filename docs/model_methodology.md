# Leakage-free historical feature pipeline

The pipeline is implemented in src/team_identity.py, src/build_features.py, and src/evaluate_models.py. Outputs are regenerated from the parsed match table; no feature value is manually entered.

## Team history and identity

OpenFootball source team strings vary between seasons. src/team_identity.py strips the three-letter country suffix, normalizes accents and common legal suffixes, and applies a small explicit alias table to club variants observed in these files. The resulting mapping is exported to data/metadata/team_aliases.csv for review. These are project-derived keys, not official club IDs; questionable mappings should be corrected before any more analysis.

The history window begins with the first included match in 2015/16. A new team starts with zero prior matches and missing rate features. Preprocessing imputes those rates from the training period only; prior-match counts remain explicit.

## What is available to each match

Features are produced in date order. For every calendar date, all match features are calculated from state at the start of that date. Results from that date update state only after its feature rows have been created. This means even an earlier 18:45 match is not used for a 21:00 match on the same date; the conservative rule avoids timezone ambiguity.

- Model A: historical team performance. Prior UCL match count, points per match, goals for/against per match, goal difference per match, win/draw rates, and home-team-at-home / away-team-away points rates. Only matches dated earlier than the row's match contribute.
- Model B: Elo. Model A plus home-minus-away Elo with a fixed +60 home-advantage adjustment. New clubs start at 1500; after each date, Elo updates use only the 90-minute H/D/A result, K=24, and the standard logistic expected score. Penalty winners do not replace the regulation result.
- Model C: recent form. Model B plus points per match and goal difference per match across up to the five most recent earlier UCL matches for each team. Form carries across season boundaries.
- Model D: player attributes. Not yet implemented. It requires an audited historical FIFA/SoFIFA data file, timestamped ratings no later than kickoff, validated player/team joins, and explicit separation between snapshot squad proxies and actual starting lineups.

Extra-time goals, shootout scores, final tables, later matches and current-season outcomes do not enter the features.

## Estimator and splits

The selected model family is regularized multinomial Logistic Regression (shared C=0.003, L2, fixed seed), preceded by median imputation and standard scaling in one scikit-learn Pipeline. C=0.003 was selected from a common validation-only grid for Models A–C based on log loss and multiclass Brier; see docs/model_c_draw_diagnosis.md. The initial C=1 outputs are preserved under data/results/initial_c1/. The pipeline is fitted on training rows only for each split. The baseline predicts H/D/A class frequencies calculated from the training period; its majority class is used for accuracy/F1. A separate fixed-configuration Random Forest validation-only comparison is supplementary and did not change model selection; see docs/random_forest_validation_experiment.md.

- Validation: train 2015/16–2020/21 (744 matches), evaluate 2021/22–2022/23 (250 matches).
- Final test: refit through 2022/23 (994 matches), evaluate 2023/24–2025/26 (503 matches).

The final test is scored only after the selected configuration is frozen; do not use it for further model or feature selection. Model variants are evaluated on common rows. Exact match assignments are exported to data/metadata/evaluation_split_assignments.csv and the selected configuration is saved in data/results/model_config.json. See docs/model_results.md for current results and docs/model_c_draw_diagnosis.md for validation-only selection.

## Manual-fixture inference artifacts

`src/export_prediction_models.py` exports separate Model A/B/C pipelines under `data/models/` for the Streamlit manual-prediction page. Each pipeline uses the shared `make_estimator()` constructor and is fitted only on the same 994 final-training rows through 2022/23. It does not fit on the 503 final-test labels or choose new features/hyperparameters. It is an operational inference artifact, not a new evaluation result.

`src/build_features.py` also writes `data/processed/team_state_snapshot.json`, whose date is the latest processed match date (currently 2026-05-30). The snapshot contains accumulated team/venue performance, current Elo and up-to-five recent results. `src/predict_fixture.py` uses the existing feature helper functions to create Model A/B/C columns for a user-selected future date strictly after that snapshot. Thus the fitted model is fixed through 2022/23, but the future fixture's historical-state inputs can use already-completed 2023/24–2025/26 matches. These outcomes update only the state; they do not fit the pipeline or select the model. This is valid for a sequential future forecast and should not be conflated with the final-test metrics.

The app calls the saved pipeline's `predict_proba()` and verifies model/data artifact hashes. See `docs/fixture_prediction.md` for the inference contract, current-state staleness, manual fixture limitations and source-access review. The production interface is not an official fixture validator and does not load 2026/27 results, injuries or lineups.

