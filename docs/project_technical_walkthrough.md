# UEFA Champions League Match Outcome Predictor

## Technical walkthrough and defense study guide

This document explains the repository as it exists now. It describes actual code paths and saved artifacts, and calls out unresolved or unknown behavior instead of filling gaps with assumptions. The project title is **UEFA Champions League Match Outcome Predictor**. The research question in the current README and app is a proposed refinement and has not been formally resubmitted. The primary target is home win, draw, or away win after 90 minutes; advancement through extra time or penalties is outside the current model.

## 1. Overall project architecture and complete data flow

The repository has five connected paths: source preservation, parsing and historical feature construction, chronological modeling/evaluation, production-pipeline export for future manual fixtures, and Streamlit presentation. The historical evaluation remains a batch experiment; the newly added manual prediction flow is a separate inference path using saved scikit-learn pipelines and a dated state snapshot.

```text
OpenFootball season files (Football.TXT)
             │
             ▼
     data/raw/ucl_YYYY-YY.txt
             │ src/parse_football_txt.py
             ▼
 data/processed/ucl_matches.csv ───────► data/metadata/ucl_source_manifest.csv
             │ src/build_features.py                 (URLs, hashes, counts, date ranges)
             ▼
 data/processed/historical_features.csv
             ├── src/evaluate_models.py
             │      ├── data/metadata/evaluation_split_assignments.csv
             │      ├── data/results/{metrics,predictions,confusion_matrices,
             │      │                 calibration_bins,model_config}.*
             │      └── reports/figures/calibration_test.png
             ├── src/diagnose_model_c_draws.py
                    └── data/results/validation_*.csv and manifest.json

 historical_features + team_state_snapshot
             └── src/export_prediction_models.py
                    └── data/models/{model_a,model_b,model_c}.joblib + manifest
                              │
                              ▼
                 app.py → saved model.predict_proba() on a manual fixture

 data + saved outputs ──► app.py ──► research narrative, historical explorer, manual inference
 notebooks 01–03 ───────► environment checks and descriptive exploration (separate from model fit)
```

`src/parse_football_txt.py` converts text fixtures/scores into one structured row per match and writes a source manifest. `src/build_features.py` normalizes names, creates match IDs, accumulates each club's pre-match history, and now writes `team_state_snapshot.json`. `src/evaluate_models.py` explicitly selects numeric feature columns, fits the evaluation estimators on chronological training slices, and writes probabilities/metrics. `src/diagnose_model_c_draws.py` is a separate validation-only diagnostic. `src/export_prediction_models.py` fits the frozen A/B/C configuration on the 994 final-training rows and saves pipelines; its manifest states that zero final-test rows were used to fit. `src/predict_fixture.py` builds one feature row from the state snapshot and calls the stored estimator's `predict_proba()`. The app reads both historical outputs and those saved inference assets; it does not fit models on app startup.

The two notebooks are not the main production pipeline. Notebook 03 is descriptive EDA over the parsed match table. Notebook 02 includes a small raw-file download/inspection workflow and has code that writes to existing raw paths. The scripts in `src/` implement parsing, feature generation, evaluation, validation diagnostics, inference-asset export, and fixture-time feature/probability construction.

## 2. Repository structure: important files and artifacts

### Root files

| Path | Purpose and actual role |
|---|---|
| `README.md` | Project synopsis, proposed question, current status, commands and links to docs. The displayed clean-install command relies on `requirements.txt`; see the dependency-file caveat in section 13. |
| `app.py` | Streamlit research narrative, historical error explorer, and manual fixture interface. It loads saved sklearn pipelines and executes real `predict_proba()` for a selected model/fixture. |
| `requirements.txt` | A pinned environment snapshot containing Jupyter, analysis libraries, XGBoost and Streamlit. The malformed final package line was split into valid XGBoost and Streamlit entries. |
| `01_environment_check.ipynb` | Executed check of Python and package imports in the project `.venv`. Its stored output reports Python 3.12.3, NumPy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1 and XGBoost 3.4.1. XGBoost is not used by the current evaluator. |
| `02_data_exploration.ipynb` | Raw-file preview and data exploration notebook. Its executed cells download the 2024/25 and 2025/26 Football.TXT files directly into `data/raw/`; rerunning those cells overwrites those paths. Later notebook cells are unexecuted in the checked-in notebook. |
| `03_exploratory_analysis.ipynb` | Executed descriptive analysis of coverage, parsing quality, H/D/A outcomes, goal patterns, format/phase patterns, and team-season points per match. It does not train the predictive models. Charts are embedded in notebook output. |

### Source code

| Path | Important functions/components | What it does |
|---|---|---|
| `src/parse_football_txt.py` | `parse_file(path)`, `main()` | Parses dates, headings, kickoff times, team labels and score notation; checks header counts/date ranges; writes the match CSV and source manifest. |
| `src/team_identity.py` | `team_key(source_name)`; `ALIASES` | Strips country codes, normalizes Unicode/punctuation/tokens, then applies explicit cross-season aliases. These are project keys, not authoritative club IDs. |
| `src/build_features.py` | `per_match_summary`, `venue_points`, `recent_summary`, `build()` | Builds chronological team states and feature rows. Contains Elo constants and same-day state-update behavior. |
| `src/evaluate_models.py` | `probabilities_for`, `metric_row`, `class_priors`, `fit_predictions`, `calibration_rows`, `main()` | Defines A/B/C feature lists, train-only preprocessing/classifier fit, baseline and metrics; exports exact splits and all evaluation results. |
| `src/diagnose_model_c_draws.py` | `probabilities`, `evaluate`, `calibration_rows`, `main()` | Uses only 2015/16–2022/23 data (744 train, 250 validation rows) to diagnose draw predictions and compare selected alternatives. Its manifest states final-test rows are not retained. |
| `src/predict_fixture.py` | `build_fixture_features`, `predict_fixture` | Builds A/B/C-compatible columns from a stored future-date team state, rejects invalid same-team/cutoff requests, calls the fitted pipeline and reorders probabilities to H/D/A. |
| `src/export_prediction_models.py` | `sha256`, `main()` | Re-fits A/B/C with the evaluation pipeline constructor on the 994 frozen final-training rows and saves joblib artifacts plus a provenance manifest; it does not select or fit on final test. |
| `tests/test_prediction_inference.py` | `PredictionInferenceTests` | Standard-library unit tests for feature formulas, cold starts, date cutoff, same-team rejection, exact feature order and probability class order. |
### Data and documentation directories

| Directory/path | Contents and meaning |
| reports/random_forest_validation/ | Separate validation-only Random Forest A/B/C metrics, confusion matrices, predictions, comparison table and provenance manifest. These do not replace or overwrite frozen evaluation files under data/results/. |
|---|---|
| `data/raw/` | Eleven preserved OpenFootball Football.TXT files, one per season 2015/16 through 2025/26. These are source text, not model-ready rows. |
| `data/processed/ucl_matches.csv` | 1,497 parsed matches, 19 columns. This includes labels, regulation and listed final scores, shootout scores, phase/format, original team strings and raw source references. |
| `data/processed/historical_features.csv` | 1,497 rows and 44 columns. Contains IDs, dates, descriptive context, target/scores, team keys and all pre-match historical feature values. Model inputs are narrower, selected lists in `evaluate_models.py`. |
| `data/processed/team_state_snapshot.json` | Current terminal state for each team key, including cumulative/venue totals, Elo, last five results, and `as_of_date`. Used only for future-date fixture inference. |
| `data/metadata/ucl_source_manifest.csv` | Per-season URL, SHA-256, byte size, declared/parsed match counts, parsed team count and date coverage. URLs reference the OpenFootball `master` path; no repository commit is pinned. |
| `data/metadata/team_aliases.csv` | Mapping from 126 distinct source labels to 100 normalized team keys. Useful for reviewing collapses/aliases; not an official identity registry. |
| `data/metadata/evaluation_split_assignments.csv` | One row per match with `match_id`, season/date and the validation/final assignment. Exactly supports the season-based cutoffs used by the evaluator. |
| `data/results/` | Selected C=0.003 evaluation metrics, predictions, confusion matrices, calibration bins, model config and validation-only draw diagnostics. Fitted inference estimators are saved separately under `data/models/`. |
| `data/results/initial_c1/` | Historical C=1 run's metrics, predictions, confusion matrices, calibration bins and config, retained for transparency. |
| `data/models/` | Three serialized sklearn pipelines for manual inference and `prediction_model_manifest.json` with training boundary, feature lists and SHA-256 hashes. These are not additional evaluation results. |
| `reports/figures/calibration_test.png` | Current selected run's final-test one-vs-rest calibration/reliability plot, generated by the evaluator. |
| `reports/figures/initial_c1/calibration_test.png` | Same chart for the original C=1 run. |
| `docs/` | Research design, parsing/feature/model/results explanations, SoFIFA research, rubric analysis, references, AI disclosure, defense preparation and this walkthrough. |
| `src/__pycache__/`, root `__pycache__/`, `.venv/` | Generated bytecode and local Python environment; not analytical source or necessary project evidence. The environment is not included in a normal portable hand-in. |

There is no `.git/` repository in the inspected checkout. There is no player ratings CSV or match-lineup file in `data/`; SoFIFA work is source research documented in `docs/sofifa_research.md`, not a model input.

## 3. Data collection: sources, raw format, parsing and validation

### Source and row meaning

The match source is the [OpenFootball Champions League repository](https://github.com/openfootball/champions-league), in [Football.TXT](https://openfootball.github.io/spec/) text format. Each output row represents a single scheduled UCL match, with home and away teams, not a team-match row or a player appearance. Eleven raw files cover 2015/16–2025/26. This is main competition coverage; qualifying rounds are not included.

The source manifest records each raw file's URL, hash and file-level counts/ranges. The URL points to a mutable `master` branch path, so the local SHA-256 hash is the strongest exact-byte provenance in this checkout; the upstream source revision is unknown/unpinned. Header agreement checks the parse against OpenFootball's declared count, not against a second official results provider.

### Parsing path in `src/parse_football_txt.py`

`parse_file` derives the season from a filename such as `ucl_2015-16.txt`. It reads the header's `# Date` range, falling back to July-to-June season bounds if the range is absent. The parser then walks lines, retaining current stage/date/kickoff context:

1. Blank, `#` comment and `=` title lines are skipped.
2. A `▪` line updates `current_stage` and resets the current kickoff time.
3. A date line updates `current_date`. Dates that omit a year are placed within the raw file's declared range, which handles the 2019/20 August 2020 restart.
4. A line starting with `HH:MM` updates `current_time`; subsequent fixture lines with no repeated time inherit it until a date or stage reset.
5. `MATCH_RE` separates home string, away string and trailing score text around the Football.TXT `v` marker.
6. Score tokens are parsed by `SCORE_RE`. Ordinary scores are treated as regulation scores. For AET, the documented parenthetical breakdown is used to identify regulation score; a 0–0 AET score is treated as 0–0 in regulation if no separate score is given. For penalties, shootout score is stored separately and, when the AET breakdown supplies enough groups, the regulation score is taken from the source's regulation component. Ambiguous regulation outcomes are left missing, not guessed.
7. `outcome_90m` is `H` when regulation home goals exceed away goals, `A` when lower, else `D`. Extra-time/final and shootout values remain separate fields.
8. Competition phase is inferred from stage text using keyword tests (group/league, playoff, final/round/quarter/semi); format era is assigned by season start year (`>=2024` means 36-team era).

`main()` checks parsed row count against each source `# Matches` header, rejects rows outside the header date range, sorts output and writes `ucl_matches.csv`. It creates `ucl_source_manifest.csv` with SHA-256 and counts. Reported parse checks: 1,497 rows, 1,497 nonmissing 90-minute outcomes and zero duplicate `(date, home_team, away_team)` keys. One known limitation: unrecognized non-fixture lines are skipped; a dropped fixture should ordinarily be caught by header-count mismatch, but count agreement is not proof of semantic correctness or official completeness.

### Coverage and observed data issues

Season counts are 125 matches each for 2015/16–2018/19; 119 for pandemic-altered 2019/20; 125 each for 2020/21–2023/24; and 189 each for 2024/25 and 2025/26. The latter format includes 144 league-phase matches, 16 playoff matches and 29 other knockouts. The old 32-team era has 96 group-stage and 29 knockout matches per regular season; 2019/20 has 23 listed knockouts due to the altered schedule.

The parsed table has 19 columns. `penalty_home_score` and `penalty_away_score` are missing for 1,489 matches because only eight rows are penalty shootouts; those nulls are expected structural absence, not failed target parsing. All core targets, dates, teams and stage values are present in the inspected file. The raw source includes kickoff times, but this project's leakage policy uses date-level availability rather than time-of-day ordering.

## 4. Data preprocessing: transformations and justifications

Preprocessing occurs in stages; “preprocessing” does not mean every column is transformed in one pandas step.

### Parsing and derived labels

- Football.TXT score strings become numeric regulation goals, separate listed post-extra-time goals and separate shootout goals. This preserves the intended 90-minute target.
- `outcome_90m` is derived from regulation goals only. `build()` rechecks that its target agrees with the parsed regulation score.
- `season`, `date`, `kickoff_time`, `stage`, `competition_phase` and `format_era` preserve temporal/competition context for splits, analysis and display.
- `source_file` and `source_line` preserve lineage. `match_id` is source file stem plus source line, e.g. `ucl_2015-16:11`; it supports reproducible row linkage, not cross-source identity.

### Team identity

`team_key()` removes a trailing three-letter country code in parentheses, applies Unicode NFKD decomposition and removes combining accent marks, lowercases, turns `&` into `and` and hyphens into spaces, tokenizes alphanumeric text, removes selected legal/structural tokens and numeric tokens, then applies the `ALIASES` dictionary. The result links source spelling variations across seasons for accumulating history.

This is a heuristic and small curated mapping, not an official club ID. Removing common tokens/numbers can theoretically merge distinct labels; incorrect aliases would contaminate team history and Elo. `team_aliases.csv` should be reviewed as data, not treated as proof that every identity is correct.

### Modeling-time imputation and scaling

Rate features are `NaN` when a club has no earlier observations; explicit prior-match counts remain zero. `SimpleImputer(strategy="median")` and `StandardScaler()` are placed in the same scikit-learn pipeline as Logistic Regression. Calling `.fit(train[features], train.outcome_90m)` ensures their medians and means/standard deviations are estimated from that training slice only; `predict_proba` applies those training parameters to validation/test. This avoids fitting transformations on future score rows.

No categorical encoding or feature selection is present in the evaluator. Team names, scores, IDs and outcome-derived columns are not included in `A_FEATURES/B_FEATURES/C_FEATURES`. There is no class rebalancing in the selected model. The balanced-weight alternative is confined to the validation diagnostic.

## 5. Exploratory data analysis: investigations and findings

The main executed descriptive notebook is `03_exploratory_analysis.ipynb`; it reads `ucl_matches.csv` and `ucl_source_manifest.csv`, and explicitly warns that full-archive summaries are descriptive, not prediction performance. It investigates:

- Per-season date range, row count, missing targets, distinct team names, source-header agreement and duplicate/core-field checks.
- H/D/A counts and proportions overall and by season.
- Goal distributions and average goals for home and away sides.
- Outcome proportions and sample sizes by old/new format and phase.
- Team-season points per match, restricted to team-seasons with at least 12 appearances.

Project-specific descriptive values from the current CSV: across 1,497 matches, outcomes are H=706 (47.16%), D=298 (19.91%), A=493 (32.93%). Mean regulation goals are 1.733 for the home side and 1.359 for the away side (3.092 total). These pooled rates motivate a frequency reference and show an aggregate home-result advantage; they do not prove a causal home effect or guarantee future-period class shares. Outcome shares vary by season: e.g., H is 53.6% in 2015/16 and 40.8% in 2020/21; D share ranges from 13.8% in 2024/25 to 26.4% in 2016/17. The 2024/25 phase structure and sample sizes differ from earlier seasons.

The notebook's team-season points ranking uses complete season results and raw team labels (aliases are not merged there). It is therefore a descriptive illustration, not a legal pre-match feature and not a ranked list that the prediction model learns from. The notebook warns that the new league phase differs structurally from the old group stage and that small knockout groups should not support strong comparisons.

`02_data_exploration.ipynb` shows the raw Football.TXT layout (headers, stages, dates, repeated kickoff time, team lines and parenthetical halftime scores) and includes download code for 2024/25 and 2025/26. It is not the executed primary EDA. Its download cell overwrites those raw filenames; avoid rerunning it inadvertently when preserving provenance. `01_environment_check.ipynb` is about runtime/package imports, not empirical analysis.

## 6. Feature engineering: every modeled feature and leakage controls

`build_features.py` first sorts match history into calendar dates. It computes each date's feature values from state accumulated before that date, stores outcomes in a temporary list, and only then updates states. This deliberately treats simultaneous or same-day fixtures as if neither result was known for the other. It is more conservative than using earlier kickoff time on that date and avoids timezone/availability assumptions. On an earlier date, all included UCL results can contribute, regardless of whether they were in an earlier season; no league results or external ratings are included.

Let a club's accumulated earlier UCL matches be (N), points (P), goals-for (GF), goals-against (GA), wins (W), draws (D). Points use 3 for a win, 1 for a draw, 0 for a loss, and all statistics use only 90-minute outcome/goals. The following are computed separately for the home and away club:

| Feature(s) | Calculation in code |
|---|---|
| `home_prior_matches`, `away_prior_matches` | (N), the number of previous UCL matches. Remains 0 for a cold-start team. |
| `*_points_per_match` | (P/N), missing when (N=0). |
| `*_goals_for_per_match` | (GF/N), missing when (N=0). |
| `*_goals_against_per_match` | (GA/N), missing when (N=0). |
| `*_goal_diff_per_match` | ((GF-GA)/N), missing when (N=0). |
| `*_win_rate`, `*_draw_rate` | (W/N), (D/N), missing when (N=0). |
| `home_team_home_prior_matches` | Number of earlier home fixtures for the home club. |
| `home_team_home_points_per_match` | Home club's points in prior home fixtures / its prior home fixture count; `NaN` if none. |
| `away_team_away_prior_matches` | Number of earlier away fixtures for the away club. |
| `away_team_away_points_per_match` | Away club's points in prior away fixtures / its prior away fixture count; `NaN` if none. |
| `elo_home`, `elo_away` | Each team's pre-date Elo, default 1500 for a new club. Saved to the feature table, but not individually included in B/C. |
| `elo_difference` | `elo_home - elo_away + 60`. The +60 is the fixed home advantage in rating points. This is the only Elo column in model B/C. |
| `home_recent_matches`, `away_recent_matches` | Count in that club's deque of up to 5 earlier UCL results; 0 for no recent history. |
| `*_recent5_points_per_match` | Mean 3/1/0 points over up to the five latest earlier UCL results; `NaN` with none. |
| `*_recent5_goal_diff_per_match` | Mean goal difference from that team's perspective over the same up-to-five results; `NaN` with none. |
| `recent5_points_difference` | Home recent points-per-match minus away recent points-per-match; `NaN` if either side is missing. |
| `recent5_goal_diff_difference` | Home recent GD-per-match minus away recent GD-per-match; same missingness rule. |

Elo begins at 1500. For one match, expected home score is (1/(1+10^{-((R_H+60-R_A)/400)})); actual score is 1.0 for H, 0.5 for D, 0.0 for A. Change is (24(actual-expected)) for home and the negative change for away. K=24. Daily changes are accumulated and applied after that date, so same-day results do not affect other same-day features. No goal-margin multiplier or decay is implemented. The code's rating update uses the 90-minute result and regulation goals only; shootout winner never replaces H/D/A.

`Model A`'s selected inputs are the 18 cumulative/venue fields: seven home, seven away and two venue counts/rates for each side. `Model B` adds `elo_difference` (19). `Model C` adds eight recent-form inputs (three home, three away, and two differences; 27 total). Model C therefore contains redundant summaries: recent values overlap in concept with cumulative features, and differences are derived from component rates. The validation correlation report finds strong pairwise correlations, including `home_prior_matches` and `home_team_home_prior_matches` around 0.999 and points-per-match with win-rate around 0.97. L2 regularization shrinks coefficients, but these correlations do not alone prove the cause of draw failures.

Data columns `match_id`, season/date, phase/era, team labels/keys, scores and `outcome_90m` are carried in feature CSV for traceability; they are not members of `FEATURE_SETS`. Model D has no features in code. No FIFA/SoFIFA rating, club snapshot, lineup or player participation variable was joined.

## 7. Dataset splitting: exact periods, sizes and reasoning

`src/evaluate_models.py` selects rows by season strings, not random sampling. Each model uses the same rows and feature variants for a given evaluation period. `data/metadata/evaluation_split_assignments.csv` records every match's role.

| Role | Seasons | Rows | Use |
|---|---|---:|---|
| Validation training | 2015/16–2020/21 | 744 | Fit preprocessing, baseline priors and candidate estimators for validation. |
| Validation | 2021/22–2022/23 | 250 | Compare configurations/features, diagnose draw probabilities and select C. |
| Final training | 2015/16–2022/23 | 994 | Refit the selected configuration before final scoring. |
| Final test | 2023/24–2025/26 | 503 | Report the frozen selected model's later-period performance. |

Rows split into validation-only train/validation or final train/test; the final train includes the validation seasons. Since the evaluator computes pre-match features chronologically across the whole archive, a later test match can legitimately have earlier matches from validation seasons in its historical team/Elo/form state. The supervised estimator and imputer/scaler are refit on each evaluation training block. This simulates learning on accumulated historical UCL match outcomes. Splits are whole seasons, which prevents same-season matches being divided between train and score sets.

The reasoning is temporal realism and fair common-row comparison, not random i.i.d. sampling. There is an important operating assumption: `historical_features.csv` is built in chronological order across the full archive, so a later validation/test match's team/Elo/form state can include outcomes of earlier matches in that same validation/test window. This is valid for a **sequential updating** forecast: after each match ends, its result becomes history for the next date. It is not a fixed-origin batch forecast where every match in a two- or three-season test block must use only history available at the first day of that block. The evaluator fits model coefficients once per period, but pre-match team-state features continue to update from earlier observed results. The app does not expose this nuance prominently; it is important to state in a defense.

The design also has limits: there is one validation window and one final period, outcomes within seasons/teams are dependent, and final test crosses the 2024/25 competition-format change. The original C=1 test results were inspected/reported before the validation-selected C=0.003 run, so the later C=0.003 test score is not an untouched test in a strict historical sense. Treat final results descriptively; do not use them for further selection.

## 8. Baseline and Models A, B and C

### Shared estimator training

`fit_predictions(train, score, features, logistic_c)` constructs `SimpleImputer(median) → StandardScaler → LogisticRegression`. It calls `fit` only on `train`; probabilities are made on the score set and reordered to fixed class order `[H,D,A]` using `probabilities_for()`. Logistic Regression uses multinomial probabilities (scikit-learn's multiclass formulation), `solver="lbfgs"`, `max_iter=2000`, `random_state=335`, default L2 penalty, no class weights. It predicts continuous H/D/A probabilities. The hard prediction for accuracy/confusion is simply `argmax`, with no custom threshold.

### Baseline

`class_priors(y)` calculates training proportions in fixed H/D/A order. `main()` tiles that vector for every scored match. The baseline gives every match identical probabilities; it uses no team or match-specific feature. Its majority class therefore becomes H in these training samples, so the baseline predicts home for every row under argmax. This is a simple marginal probability floor, not a model of venue-specific home advantage or the best possible benchmark.

### Incremental model groups

| Model | Inputs | Increment over previous group |
|---|---|---|
| A | 18 historical team/venue features described in section 6 | Team-specific cumulative UCL record through the previous date. |
| B | A + `elo_difference` | A sequential rating contrast initialized at 1500 and with +60 home adjustment. |
| C | B + eight recent-form columns | Up to five prior UCL results' points and goal-difference summaries and their home-away differences. |
| D | Not implemented | Intended C + historical FIFA/SoFIFA player aggregates; no D results exist. |

The original model family is held constant across A/B/C to focus that ablation on input groups. Feature count grows from 18 to 19 to 27. A separate fixed 500-tree Random Forest challenger used median imputation and the same A/B/C feature groups on the established 744/250 train-validation split; it is supplementary and did not replace the selected Logistic Regression models. RF A slightly improved macro F1 but Model C retained lower log loss and Brier. See docs/random_forest_validation_experiment.md. The research question does not presuppose feature value. Final-test metrics have prior C=1 exposure and are not pristine; small differences are not robust without uncertainty analysis.

## 9. Model selection and regularisation

In Logistic Regression, `C` is inverse regularization strength: smaller C means stronger L2 shrinkage. The original experiment used C=1. Because Model C assigned no validation match a draw argmax and probability metrics were weak, `src/diagnose_model_c_draws.py` trained A/B/C on the 744 training rows over the shared grid `[0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10]`. It also examined class-balanced weights at selected C values and C plus an absolute Elo-strength gap. All diagnostic choices used only validation.

C=0.003 had the lowest validation log loss and Brier for each A/B/C, so the common value was selected to preserve a controlled comparison. This is one 250-match selection window and may overfit validation; it is not a universal optimum. The baseline's training class priors are likewise learned from its training slice. No feature selection, threshold adjustment or probability calibration post-processing is implemented.

Validation comparison (lower log loss/Brier is better):

| Validation configuration | Log loss | Brier | Accuracy | Predicted H / D / A |
|---|---:|---:|---:|---:|
| Baseline | 1.0475 | 0.6330 | 0.468 | 250 / 0 / 0 |
| A, C=0.003 | 0.9620 | 0.5685 | 0.552 | 132 / 0 / 118 |
| B, C=0.003 | 0.9578 | 0.5661 | 0.560 | 136 / 0 / 114 |
| C, C=0.003 | 0.9491 | 0.5599 | 0.564 | 134 / 0 / 116 |
| C, C=0.003, balanced weights | 0.9811 | 0.5824 | 0.540 | 110 / 13 / 127 |
| C + absolute Elo gap, C=0.003 | 0.9489 | 0.5595 | 0.568 | 135 / 0 / 115 |

Balanced weighting produced 13 draw argmaxes but only 5.8% draw recall and worse primary metrics/accuracy than unweighted C=0.003; it was not selected. Adding absolute Elo gap changed validation scores by only about 0.0002 log loss and 0.0004 Brier and still produced no draw argmax; it was also rejected. No threshold was moved to inflate draw accuracy. The final evaluator defaults `--logistic-c` to 0.003 and writes that choice to `data/results/model_config.json`.

## 10. Evaluation: metrics, files, chart and errors

### Metrics and exact conventions

- **Multiclass log loss:** evaluator takes the probability assigned to the actual H/D/A result, clips it to `[1e-15, 1]`, computes negative natural log and averages across matches. Lower is better; a confident wrong probability incurs a large penalty. This is the primary score.
- **Multiclass Brier score:** for each match, code makes a three-element one-hot actual vector, sums squared differences for H, D and A, then averages the sums across matches. It does not divide the per-match sum by three. Lower is better; it evaluates the full probability vector. This is the second primary score.
- **Accuracy:** fraction where highest probability class equals actual class. It discards probability magnitude and is secondary.
- **Precision/recall/F1:** computed for each class using H/D/A label order, plus macro averages. `zero_division=0`; a class never predicted receives zero precision/F1 rather than a warning/undefined value.
- **Confusion matrix:** actual class by predicted argmax class, with fixed H/D/A ordering.
- **Calibration:** one-vs-rest for each class. Final-test predicted probabilities are divided into up to five quantile bins using `pandas.qcut` (duplicate boundaries can reduce bin count). Each bin records count, mean predicted probability and observed class frequency. The chart plots observed frequency vs mean prediction and the ideal diagonal. It is a descriptive reliability plot, not a formal calibration test or recalibration step.

### Saved outputs

| Output | What is in it |
|---|---|
| `data/results/metrics.csv` | 28 rows: overall validation/final metrics and final-test format/phase metrics. Columns include n, log loss, multiclass Brier, accuracy, macro and H/D/A precision/recall/F1. |
| `data/results/predictions.csv` | 3,012 records: each of four systems (baseline and A/B/C) on 250 validation and 503 final-test matches; includes actual, argmax, and `p_H/p_D/p_A`. It does not include Model D. |
| `data/results/confusion_matrices.csv` | 72 counts: every actual/predicted H/D/A cell for four models in each of two periods. |
| `data/results/calibration_bins.csv` | 48 rows of final-test one-vs-rest quantile reliability bins for baseline and A/B/C. |
| `data/results/model_config.json` | C, solver, max iterations, seed, class order, train-only imputer/scaler descriptions, feature lists, split seasons/sizes, primary metrics and split manifest path. It is configuration metadata; no trained model weights are saved. |
| `data/results/initial_c1/*` | Same output types for the original C=1 evaluation, retained for transparency. |
| `reports/figures/calibration_test.png` | Three side-by-side one-vs-rest reliability plots for H, D and A. The line is the ideal calibration diagonal; model lines come from saved final-test quantile bins. |
| `data/results/validation_draw_diagnostics.csv` | Validation metrics/class counts/mean probabilities for baseline, A/B/C across regularization, weighting and gap-feature variants. |
| `validation_draw_confusions.csv`, `validation_draw_calibration.csv`, `validation_draw_probability_summary.csv` | Validation-only class confusions, quantile reliability summaries, and probability distributions by actual class. |
| `validation_draw_errors.csv` | Validation prediction errors with match identity, class probabilities and max probability. |
| `validation_class_balance.csv`, `validation_feature_by_outcome.csv`, `validation_train_feature_correlations.csv` | Training/validation class shares, outcome-conditioned feature summaries, and training-only correlation pairs with absolute Pearson r ≥ 0.70. |
| `validation_draw_diagnostic_manifest.json` | Diagnostic seasons/counts, the explicit `final_test_rows_retained: false` and the considered model specs. |

Current selected C=0.003 aggregate scores:

| Period | Model | n | Log loss | Multiclass Brier | Accuracy | Macro F1 |
|---|---|---:|---:|---:|---:|---:|
| Validation | Baseline | 250 | 1.0475 | 0.6330 | 0.4680 | 0.2125 |
| Validation | A | 250 | 0.9620 | 0.5685 | 0.5520 | 0.4071 |
| Validation | B | 250 | 0.9578 | 0.5661 | 0.5600 | 0.4128 |
| Validation | C | 250 | 0.9491 | 0.5599 | 0.5640 | 0.4153 |
| Final test | Baseline | 503 | 1.0217 | 0.6167 | 0.4990 | 0.2219 |
| Final test | A | 503 | 0.9308 | 0.5485 | 0.5865 | 0.4224 |
| Final test | B | 503 | 0.9324 | 0.5492 | 0.5825 | 0.4199 |
| Final test | C | 503 | 0.9306 | 0.5481 | 0.5825 | 0.4198 |

The new league phase begins in 2024/25 and has different match/opponent structure. Final-test phase n values are old-era group phase 96, old-era knockout 29, new league phase 288, new-format knockout playoff 32 and other knockout 58. The small 29/32 samples do not support strong phase ranking. The saved phase metrics are exploratory, not evidence that format itself causes performance differences.

### Error interpretation

Selected Model C final test has 251 actual H, 87 D and 165 A; argmax predicts H=287, D=0 and A=216. C's draw precision, recall and F1 are all zero. C mean probabilities H/D/A are 0.452/0.191/0.357; observed frequencies are 0.499/0.173/0.328. The model assigns some draw probability, but never more than both alternatives simultaneously. Examples in `docs/model_results.md` include Bayern–Celtic 1–1 with predicted H/D/A 0.841/0.096/0.062; Man City–Feyenoord 3–3 with 0.836/0.104/0.060; Bayern–Copenhagen 0–0 with 0.827/0.105/0.068. These are high-confidence misses, not simply close argmax ties.

Final test results should be interpreted alongside Model A/B/C comparisons, per-class scores and calibration, not only accuracy. No confidence intervals or dependence-aware uncertainty estimates are saved. Therefore small numerical gains (e.g. C versus A) should not be described as statistically established.

## 11. Draw-prediction problem: diagnosis and decisions

The draw investigation is in `docs/model_c_draw_diagnosis.md` and `src/diagnose_model_c_draws.py`. The script reads only rows from the six training seasons and two validation seasons, checks 744/250 rows and eight seasons, and discards other seasons while reading. It reports `final_test_rows_retained: false`. It evaluates candidate probabilities on validation; it does not set a decision threshold.

Key diagnosis:

1. **Imbalance is present but moderate.** Train proportions are 45.4% H, 21.4% D, 33.2% A; validation 46.8/20.8/32.4. Draws are not absent or vanishingly rare.
2. **C=1 probability allocation leans away on validation.** Mean probabilities are H/D/A 0.421/0.155/0.424 versus actual 0.468/0.208/0.324. At selected C=.003 this moves closer (0.430/0.178/0.391) but still understates H and D and overstates A on that window.
3. **Calibration is noisy.** For selected C=.003, five draw-probability bins of 50 matches have predicted means 0.128, 0.156, 0.176, 0.200, 0.232 and observed draw rates 0.14, 0.22, 0.18, 0.24, 0.26. This small sample is insufficient for fine calibration claims.
4. **Draw feature values often sit between decisive outcomes.** Validation means show home historical points per match 1.351 for draws, versus 1.627 for home wins and 1.244 for away wins; mean Elo difference including home advantage is +41 for draws, +113 for home wins, and -6 for away wins. This describes association, not cause.
5. **Inputs are redundant and model is linear/additive.** Several features correlate strongly. Multinomial logistic regression has linear class log-odds and no explicit non-linear strength-closeness effect or match interaction. A new absolute Elo gap feature did not materially change probability scores or cause draw argmaxes.
6. **Regularization mattered.** C=.003 had best validation log loss and Brier for A/B/C on the common grid. Stronger L2 shrinkage reduced scores relative to C=1. It did not restore draw argmaxes.
7. **Balanced weights were rejected for the primary objective.** They created 13 draw argmaxes at C=.003 but had worse log loss, Brier and accuracy, with just 5.8% draw recall. Selecting them for more predicted draws would sacrifice the stated probability objective.

Decision: select unweighted shared C=.003 on validation, preserve ordinary argmax, and report draw failures. Do not claim the issue is solved. After freezing that setting, the evaluator generated C=.003 test results for reporting. Earlier C=1 test values had already been seen; no further test-based tuning is justified.

## 12. Streamlit architecture: sections and interactions

`app.py` sets a wide page layout and defines project paths/classes. `load_data()` is wrapped in `@st.cache_data`; it reads the processed match CSV, metrics, predictions (then filters to final test), source manifest, split CSV, model config, archived C=1 metrics and calibration PNG. It reconstructs each prediction's `match_id` from source file/line, validates a many-to-one merge to actual match names/regulation score, then derives max probability and an error boolean. If required data are absent/empty it displays an error and stops.

Navigation is a sidebar `radio` with ten conditional sections:

1. **Overview:** states the proposed question/status, target, incremental model groups and 90-minute scope. Model D is explicitly not implemented/scored.
2. **Data:** displays match/season/date/source-file/raw-size summary, per-season manifest table, full-archive outcome counts, core variables, source links and parse/completeness caveats. The archive bar chart is descriptive, not a forecast.
3. **Preprocessing:** explains regulation target parsing, same-date feature cutoff, Elo and transforms; lists feature groups and cold-start/alias limitation.
4. **Models:** presents baseline and A–D table, Logistic Regression and selected C, train-only preprocessing, and draw argmax caveat.
5. **Evaluation:** derives split counts directly from the saved split map, describes metrics and shows phase sample sizes from final predictions. Warns that test has historical exposure and should not be used for new selection.
6. **Results:** displays saved overall metrics and phase metrics; loads the saved calibration image; states selected Model C's predicted counts, draw failure and average probabilities; expander shows C=1 archived table.
7. **Predict a fixture:** loads models from `data/models/` and `team_state_snapshot.json`; visitor supplies home/away club identities, A/B/C model and a future date. Artifact hashes are checked against the model manifest. The app calls `predict_fixture()` and the selected saved sklearn pipeline's `predict_proba()`, then displays H/D/A probabilities, argmax class and exact feature inputs. It rejects a date on/before the state cutoff, rejects same-team selections, and warns that the schedule is not verified, model estimates are not guarantees, and current-season results/rosters are missing.
8. **Error explorer:** filters the final-test `predictions.csv` by A/B/C, season, phase, actual class, predicted class and minimum max-class probability. It displays up to 100 rows, lets the visitor choose a match ID and shows regulation score, actual/predicted class and three historical probabilities. A high-confidence missed draw triggers a warning. These are held-out historical predictions, distinct from manual future fixture estimates.
9. **Limitations:** lists left censoring, source validation limits, same-day rule, aliases, one validation window/no uncertainty, draw failure, phase sample sizes/format shift, absent player features/lineups, stale prediction state and no automatic schedule feed. It gives a qualified conclusion.
10. **Reproduce & references:** provides commands, points to split/config/docs, shows method/data citations and AI-use statement. The static site links directly to the published repository; the separate Streamlit app may read `UCL_REPOSITORY_URL` for its in-app link.

`load_data()` remains responsible for historical tables/plots. A separate `load_prediction_assets()` cached resource reads joblib models and JSON snapshot; it verifies the state, feature-table and model hashes against `prediction_model_manifest.json`. The app doesn't train on startup. The inference exporter refits A/B/C on 994 rows through 2022/23, while the latest state snapshot includes match outcomes through 2026-05-30. Those later completed outcomes update team state only; the classifier coefficients remain fit only through the final-training period. The app requires requested fixture date later than the snapshot. It does not confirm that the selected clubs are scheduled to play.

## 13. Reproducibility: how to recreate pipeline and results

Run from the repository root in WSL with Python 3.12. The intended command order is:

```bash
# Setup in the existing project environment
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python src/parse_football_txt.py
.venv/bin/python src/build_features.py
.venv/bin/python src/diagnose_model_c_draws.py
.venv/bin/python src/evaluate_models.py --logistic-c 0.003
.venv/bin/python src/export_prediction_models.py
.venv/bin/streamlit run app.py
```

The parser needs the eleven `data/raw/ucl_*.txt` source files already present; it does not download them. Notebook 02 can fetch only 2024/25 and 2025/26 from `master`, but overwrites those files and does not reproduce the older eight seasons. The current README says these raw inputs are preserved in the repository. For exact input provenance, check `ucl_source_manifest.csv` hashes. The data acquisition history for each file and a pinned OpenFootball commit are not established in the current tree.

The malformed last dependency entry has been split into separate XGBoost and Streamlit lines. The requirements file is still a full pinned environment snapshot with many notebook/transitive packages, not a minimal deployment requirements list. A clean environment rebuild should be verified before hand-in.

After dependencies/data are in place, the parser writes the processed match table and manifest; builder writes aliases/features/team-state snapshot; diagnostic writes validation-only outputs; evaluator writes split assignments/config/metrics/probabilities/confusions/calibration and PNG; exporter fits final-training-only pipelines to `data/models/`; and Streamlit reads the artifacts. The evaluator may overwrite historical result files. The exporter stores model coefficients together with preprocessing objects in joblib and provenance in JSON. Exact evaluation settings remain in `data/results/model_config.json`; operational inference settings/hash records are in `data/models/prediction_model_manifest.json`; split membership is per match. `tests/test_prediction_inference.py` covers inference feature and guard behavior. The published repository history begins with initial submission commit `932b50a`; earlier local development history was not included in that upload. Source-data hashes are also recorded in the manifest.

## Complete end-to-end execution flow

1. Start with the preserved 11 raw Football.TXT files in `data/raw/`; verify their SHA-256 values against the generated manifest if preserving provenance.
2. Run `src/parse_football_txt.py`. It turns line context and score notation into the 19-column, one-row-per-match CSV and writes per-season manifest data.
3. Run `src/build_features.py`. It normalizes source team labels, creates match IDs, walks matches date-by-date, uses only earlier-date results to produce 44-column rows, and checks row uniqueness and target/score agreement.
4. Run src/diagnose_model_c_draws.py for validation-only candidate comparison and diagnostic CSVs. It is explanatory/model selection support, not a final-test run. Run src/evaluate_random_forest_validation.py only to reproduce the supplementary RF comparison; it writes to reports/random_forest_validation/ and leaves frozen data/results/ files untouched.
5. Run `src/evaluate_models.py --logistic-c 0.003`. It exports the per-match split manifest; computes train class priors; fits median-imputation/scaling/logistic pipelines for A/B/C on validation training and final training; obtains probabilities; calculates metrics/confusion counts; generates final-test calibration bins/figure; and writes config/results.
6. Run `src/export_prediction_models.py`. It fits and serializes A/B/C pipelines on the frozen 994-row final-training block, writes model hashes/config, and verifies zero final-test rows entered fitting.
7. Run `.venv/bin/python -m unittest discover -s tests` to check feature formulas, cold start, date cutoff, same-team guard and probability order.
8. Launch `streamlit run app.py`. The app reads saved outputs and pipelines; users can explore historical test predictions or request a separate future-date estimate for manually selected teams.
9. Use docs/notebooks to explain source quality, feature timing, selection, errors and limits. Do not present EDA as predictive evaluation; do not use the already viewed final period for future selection.

## Glossary

| Term | Meaning in this project |
|---|---|
| 90-minute result | H/D/A outcome at regulation time, before extra time or shootout. |
| AET | After extra time. Source notation can list both the post-extra-time score and parenthetical regulation/half-time scores. |
| Argmax | Choosing the class with the largest predicted probability; used for hard classifications and confusion matrices. |
| Brier score | Mean sum of squared differences between the three predicted class probabilities and the one-hot actual outcome. |
| Calibration | Agreement between predicted probabilities and observed frequencies across probability bins. |
| Class prior | Training sample frequency of each H/D/A class; the baseline's probability vector. |
| Cold start | Club with no earlier UCL matches in the included 2015/16 onward history; rate stats are missing and counts are zero. |
| C (Logistic Regression) | Inverse regularization strength; smaller values impose stronger coefficient shrinkage. |
| Elo | Sequential rating updated from expected versus actual 90-minute result. |
| Feature leakage | A model input includes information unavailable at the assumed prediction time or derived from the target/future. |
| Final test | Later chronological 2023/24–2025/26 block used for reporting after validation selection. Historically not pristine because C=1 test scores had been seen earlier. |
| H/D/A | Home win, draw, away win labels, always ordered `[H,D,A]` in probability outputs. |
| L2 regularization | Penalty that shrinks model coefficients; controlled inversely by C. |
| Log loss | Negative log probability assigned to the actual class, averaged over matches. |
| Match ID | `source_file` stem plus source line; stable within this particular raw-file version. |
| Model A/B/C | Nested feature groups: cumulative team performance; plus Elo; plus recent form. |
| Model D | Proposed optional addition of dated FIFA/SoFIFA player aggregates; currently not implemented. |
| Multinomial logistic regression | A linear classifier that estimates a probability for each of the three mutually exclusive outcomes. |
| One-vs-rest | For each class, treat that class as positive and other two classes as negative for calibration summaries. |
| Pipeline | Scikit-learn object chaining imputation, scaling and classifier so each is fit on training rows together. |
| Quantile bin | Group of predictions with a similar ranked probability range and roughly equal row counts. |
| Regulation goals | Goals scored in the 90-minute match, excluding extra-time and penalties. |
| Same-day cutoff | All matches on one calendar day use pre-day state; results update only after all that day's feature rows. |
| Snapshot squad proxy | Aggregation of players attached to a club in a dated game-data snapshot; not proof of UCL registration or appearance. |
| Temporal left censoring | Team history before the project's 2015/16 start is unavailable, so early cumulative statistics are incomplete. |
| Validation set | 2021/22–2022/23 block used to compare configurations and select C. |
| Leakage-free fit | Imputer, scaler and estimator fit only on each chronological training sample. |

## 30 likely professor defense questions with grounded answers

1. **What is the research question?** — The current proposed refinement asks whether historical team performance, Elo, recent form and eventually player attributes improve probabilistic 90-minute H/D/A predictions, and whether results differ by league/group versus knockout phase. It has not formally replaced the submitted proposal.
2. **What does one row represent?** — One Champions League match, with home/away teams, date, regulation outcome and source-lineage fields; it is not one team or one player.
3. **Why predict the 90-minute result?** — It is the finalized primary target H/D/A. Extra-time goals, shootout and advancement are kept separate for a possible tournament simulation.
4. **Where does the match data come from?** — OpenFootball's Champions League Football.TXT files for 2015/16–2025/26, preserved under `data/raw/` and cited in `docs/references.md`.
5. **How many matches and seasons are there?** — 1,497 matches across 11 seasons. The parser reports zero missing 90-minute targets and zero duplicate date/home/away keys.
6. **What validates the parser?** — Parsed counts match each file's declared `# Matches`; dates are range-checked; labels are cross-checked against regulation scores in feature building. These checks do not independently prove the source is complete or correct against UEFA.
7. **How do you distinguish regulation, extra time and penalties?** — `parse_file()` follows Football.TXT score notation, stores regulation goals for H/D/A, keeps listed later score and penalty values separate, and leaves ambiguous regulation labels missing rather than guessing.
8. **What is a data limitation?** — Upstream revision is not pinned, source completeness is not independently audited, qualifiers are absent, 2019/20 has a pandemic-altered 119 matches, and the 2024/25 format changed.
9. **How are club names linked?** — `team_key()` strips country codes, normalizes Unicode/punctuation and structural tokens, then applies explicit aliases. It creates 100 canonical keys from 126 source spellings, but these are not official IDs and errors could merge histories.
10. **Why do you have missing features?** — A club without a previous included match has no meaningful prior rate, so rates are NaN while prior-match count is zero. The model pipeline imputes medians from training data only.
11. **What does Model A measure?** — Eighteen cumulative team/venue variables: prior match count, points/goals/goal difference per match, win/draw rates for each side, and home-at-home/away-away sample counts and points rates.
12. **How is recent form defined?** — Up to the five most recent prior UCL matches across season boundaries. It uses mean 3/1/0 points and per-match goal difference from each club's perspective, plus home-away differences.
13. **How is Elo updated?** — New sides start at 1500; expected home score uses `home Elo + 60` versus away Elo in a base-10 logistic formula; actual H/D/A is 1/0.5/0; change is K=24 times actual minus expected. Updates are applied after the calendar day.
14. **Why use a same-day cutoff?** — Every match that date gets start-of-day history. This avoids claiming that the result or data from an earlier kickoff was available for later same-day fixtures without explicit timezone/availability rules.
15. **What exactly differs between A, B and C?** — A uses 18 cumulative/venue features; B adds one Elo difference for 19; C adds eight recent features for 27. The estimator family and shared C are held constant.
16. **What is the baseline?** — Training H/D/A class proportions repeated for every scored match. It is a simple marginal-frequency probability reference; it does not learn team strength.
17. **Why Logistic Regression?** — The implementation uses a compact regularized multinomial probability model with standardized inputs and an interpretable linear/additive specification. It is one practical model choice, not claimed to be universally best.
18. **What does C=.003 mean?** — C is inverse regularization strength; .003 applies stronger L2 shrinkage than the original C=1. The shared value was selected by validation log loss and Brier for A/B/C.
19. **How were train and validation split?** — Train 2015/16–2020/21 (744); validation 2021/22–2022/23 (250). The validation diagnostic compares alternatives only on these rows.
20. **What is the final train/test split?** — Refit through 2022/23 (994) then score 2023/24–2025/26 (503). Assignments are in `evaluation_split_assignments.csv`. The features for later test dates can use results of earlier test dates, matching sequential forecasting rather than fixed-origin forecasting.
21. **Was the final test untouched?** — Not strictly: the original C=1 test results had been seen/reported before choosing C=.003 on validation. The updated C=.003 scores were generated after selection and not used for a new choice, but future tuning on this period would be inappropriate.
22. **Why prioritize log loss and Brier?** — The question is about probabilities; both score the probability assigned to the actual class/full H-D-A vector. Accuracy only checks which class is largest and ignores confidence.
23. **How is multiclass Brier calculated?** — For each match, sum squared errors for H, D and A versus a one-hot actual vector, then average those per-match sums. The code does not divide each sum by three.
24. **What does the confusion matrix show?** — It counts actual H/D/A rows against argmax predicted classes. It uses fixed class order; zero-predicted classes receive zero precision/F1 by implementation convention.
25. **Why did you choose C=.003?** — Across the shared validation grid .001 to 10, .003 minimized log loss and Brier for each A/B/C. It is selected on one 250-match period, so it may be validation-specific.
26. **Why not use balanced class weights?** — They created some draw predictions but at C=.003 only 5.8% draw recall and worse validation log loss, Brier and accuracy; the primary probability objective did not support choosing them.
27. **Why does the model miss draws?** — Draw class share is moderate, but the linear additive model and correlated cumulative/recent variables may not represent matchup closeness or draw mechanisms well. Validation also shows draw probability is understated. These are plausible contributors, not a proven causal diagnosis.
28. **What does the calibration chart show?** — For each class, grouped predicted probabilities are compared with observed frequencies on the final period. It is a visual reliability summary; there is no recalibration and no uncertainty band.
29. **Does the website provide live fixture predictions?** — The historical explorer shows saved retrospective final-test predictions. A separate manual form runs the saved A/B/C pipeline for a user-entered hypothetical pairing/date, but it does not validate the fixture or use live 2026/27 results; it is not an automated live prediction service.
30. **What would you improve next, and what about player data?** — First verify clean-install reproduction, add full historical leakage checks and uncertainty analysis, and manually review the website/defense. Model D remains optional: researched FIFA/SoFIFA snapshots are not joined or proof of actual lineups, and coverage for a common time-safe test comparison is uncertain. A current authorized automated fixture feed was not established, and the Streamlit/GitHub Pages deployment mismatch remains unresolved.
