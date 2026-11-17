# UEFA Champions League Match Outcome Predictor

An ES 335 project studying which pre-match information improves probabilistic UEFA Champions League match predictions. **Published site:** https://raghav-iit.github.io/ucl-predictor/ · **Repository:** https://github.com/raghav-iit/ucl-predictor

## Research question and target

The following is a **proposed refinement** of the submitted proposal, not formally resubmitted:

> To what extent do historical team performance, Elo-based strength ratings, recent form, and historical player attributes improve the probabilistic prediction of 90-minute UEFA Champions League match outcomes? In particular, do player-level features provide measurable improvements over team-level features, and does predictive performance differ between league-phase and knockout matches?

Target: home win (H), draw (D), or away win (A) after 90 minutes. Extra time, penalties, aggregate scores and advancement are outside the classifier. One row represents one completed main-competition fixture with date, season/stage, teams, regulation goals and outcome; extra-time and shootout scores are separate.

## Data and preparation

Preserved OpenFootball Champions League Football.TXT files in `data/raw/` cover 2015/16–2025/26. `data/processed/ucl_matches.csv` contains **1,497 matches**: 706 home wins, 298 draws and 493 away wins; qualifying rounds are excluded. The source manifest at `data/metadata/ucl_source_manifest.csv` records URLs, hashes, sizes, declared/parsed counts, team counts and date coverage.

`src/parse_football_txt.py` parses score notation and stages; ambiguous regulation scores are not guessed and shootout goals are kept separate. Checks compare source-declared and parsed counts, duplicate fixture keys, missing outcomes and season date coverage. They do not independently verify every record against UEFA. Team identities use a reviewed project alias map, not official IDs. See [data preparation](docs/data_preparation.md), [executed EDA](03_exploratory_analysis.ipynb) and [references](docs/references.md).

## Features and models

`src/build_features.py` builds date-ordered histories. All fixtures on the same date use state from before that date, and results are applied only after feature rows for that date are built. Only earlier 90-minute outcomes are used. Histories start in 2015/16 and are left-censored.

- **Baseline:** training-period H/D/A outcome frequencies.
- **Model A:** historical counts, points, goals for/against/difference per match, win/draw rates and venue-specific rates.
- **Model B:** A plus Elo difference (initial 1500, K=24, fixed +60 home adjustment).
- **Model C:** B plus points and goal-difference averages over each team's latest up to five earlier UCL matches.

A–C use median imputation, standard scaling and regularized multinomial Logistic Regression (`lbfgs`, L2, common `C=0.003`, `max_iter=2000`, seed 335). Preprocessing is fitted inside each training pipeline. C was selected on validation and shared across A–C. Logistic Regression provides a common regularized probability model for controlled comparisons, not a claim of universal optimality.

FIFA/SoFIFA data were investigated but **not included in evaluated models**. Model D is unimplemented because the available snapshots do not establish consistent pre-match dates, historical club/registration or starting lineups. Squad membership is not match participation. A fixed-configuration Random Forest was a supplementary validation-only experiment, not a replacement for A/B/C; see [RF report](docs/random_forest_validation_experiment.md) and [SoFIFA research](docs/sofifa_research.md).

## Chronological evaluation and results

| Period | Seasons | n | Purpose |
|---|---|---:|---|
| Train | 2015/16–2020/21 | 744 | Fit |
| Validation | 2021/22–2022/23 | 250 | Select regularization |
| Final test | 2023/24–2025/26 | 503 | Frozen comparison |

Models share evaluation rows. Primary metrics are multiclass log loss and Brier score (lower is better) because the task is probabilistic. Accuracy, macro F1, class precision/recall, confusion matrices and one-vs-rest calibration are secondary.

| Period | System | Log loss | Brier | Accuracy | Macro F1 |
|---|---|---:|---:|---:|---:|
| Validation | Baseline | 1.0475 | 0.6330 | 0.4680 | 0.2125 |
| Validation | A | 0.9620 | 0.5685 | 0.5520 | 0.4071 |
| Validation | B | 0.9578 | 0.5661 | 0.5600 | 0.4128 |
| Validation | C | 0.9491 | 0.5599 | 0.5640 | 0.4153 |
| Final test | Baseline | 1.0217 | 0.6167 | 0.4990 | 0.2219 |
| Final test | A | 0.9308 | 0.5485 | 0.5865 | 0.4224 |
| Final test | B | 0.9324 | 0.5492 | 0.5825 | 0.4199 |
| Final test | C | 0.9306 | 0.5481 | 0.5825 | 0.4198 |

All A/B/C models had **zero draw recall** on the final test: Model C classified 0 of 87 draws as the argmax. Small score differences have no uncertainty intervals. The final test spans the 2024/25 format change, and phase comparisons are descriptive, especially for small knockout samples. Final-test results had previously been inspected under C=1 before C=0.003 was selected using validation. The test was not used for that new selection, but is **not historically untouched**. Do not use it for further model selection.

Supplementary RF A had the highest validation macro F1 (0.4204) and classified 1/52 draws, but log loss (0.9525) and Brier (0.5637) were worse than Logistic Model C (0.9491, 0.5599); it was not selected. Details, representative errors and calibration are in [model results](docs/model_results.md) and [draw diagnosis](docs/model_c_draw_diagnosis.md).

The site’s historical explorer shows saved retrospective final-test predictions. Separate manual inference estimates a user-entered pairing from saved parameters/state through 2026-05-30. It does not verify a fixture, use live data or include a 2026/27 feed.

## Setup and reproduction

Developed in WSL with Python 3.12. From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
```

To rebuild the primary data/model outputs:

```bash
.venv/bin/python src/parse_football_txt.py
.venv/bin/python src/build_features.py
.venv/bin/python src/diagnose_model_c_draws.py
.venv/bin/python src/evaluate_models.py --logistic-c 0.003
.venv/bin/python src/export_prediction_models.py
```

Optional, supplementary validation-only RF experiment: `.venv/bin/python src/evaluate_random_forest_validation.py`.

Rebuild scripts write derived files under `data/processed/`, `data/results/`, `data/models/` and `reports/`. Back up frozen artifacts or use a fresh copy. Do not run the evaluator just to view saved results. Split assignments, configuration, predictions and metrics are in `data/metadata/` and `data/results/`.

Run the Streamlit application: `.venv/bin/python -m streamlit run app.py`. The published GitHub Pages site is a separate static HTML/CSS/JavaScript application under `docs/`; Pages does not run the Streamlit server. Preview the static site with `.venv/bin/python -m http.server 8765 --directory docs`, then open http://localhost:8765/. Export-refresh details are in [docs/github_pages.md](docs/github_pages.md). The pinned requirements describe the full notebook/app environment; a clean installation has not been independently verified.

## Limitations, references and AI use

There are no implemented 2026/27 results or automated upcoming fixtures. Other limitations include weak draw classification, left-censored histories, heuristic aliases, competition-format change, no uncertainty intervals, and prior C=1 final-test exposure. See [methodology](docs/model_methodology.md), [technical walkthrough](docs/project_technical_walkthrough.md), [rubric audit](docs/rubric_gap_analysis.md) and [defense preparation](docs/defense_preparation.md).

Sources: [OpenFootball match data](https://github.com/openfootball/champions-league), [Football.TXT specification](https://openfootball.github.io/spec/), [scikit-learn Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), and the [official ES 335 project guide](https://ml2026.floodresq.com/project-guide). More citations are in [docs/references.md](docs/references.md). AI assistance is disclosed in [docs/ai_use_disclosure.md](docs/ai_use_disclosure.md); the student must add any additional tools used outside the documented work and independently explain the implementation.

