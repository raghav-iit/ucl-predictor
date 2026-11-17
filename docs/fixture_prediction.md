# Manual fixture prediction interface

## Purpose and scope

The Streamlit app now includes a manual fixture prediction interface in addition to its project narrative and historical error explorer. The visitor selects two clubs from the historical identity map, selects Model A/B/C, enters a match date after the available state snapshot, and requests H/D/A probabilities. The app does not assert that the visitor's chosen pair/date is an official scheduled fixture.

### Requirements traced

The submitted formal proposal itself was not found in the repository or supplied attachments I could identify. I therefore distinguish it from the earlier user-supplied **project-development brief**, which explicitly requires a visitor to choose home and away teams, enter relevant match information, see probabilities and a predicted outcome, understand the prediction, and use a clean interface. That brief also names GitHub Pages and says the architecture should not rely on a continuously running local Python server or sacrifice correctness for appearance.

The official ES 335 rubric supplied in the conversation allocates 10 points to the interactive website, 5 to useful interaction, and 5 to individual understanding/defense. The rubric's website labels do not themselves specify a particular fixture-prediction form. The professor's later website instruction separately requires the site to explain the research question/row meaning, data, preprocessing, baseline/models, evaluation, results/errors, limitations and at least one useful interaction. The new interface supplements this narrative; it does not replace it.

The implemented local flow satisfies the available manual-prediction interaction by selecting home/away teams, a model and match date, then showing actual model probabilities, argmax outcome and features. Hosting compatibility remains a separate issue: Streamlit runs a Python app and is not a static GitHub Pages application. This change is local only; nothing is deployed.

## Fitted inference models and relationship to evaluation

The selection result remains the existing validation-selected regularized Logistic Regression configuration: Models A/B/C, same feature lists, `C=0.003`, L2 penalty, `lbfgs`, `max_iter=2000`, `random_state=335`, median imputation and `StandardScaler` in one scikit-learn pipeline. `make_estimator()` in `src/evaluate_models.py` is shared by the evaluator and exporter so inference fit construction cannot drift in preprocessing or classifier settings.

`src/export_prediction_models.py` fits the three saved pipelines on the existing final-training rows only: 2015/16–2022/23, 994 matches. It verifies that the expected 503 final-test rows are present but fits on zero of them. It does not search hyperparameters, alter features, calibrate probabilities, or change evaluation outputs. Files are saved under `data/models/` with `prediction_model_manifest.json` recording model hashes, feature lists, training cutoffs, C, versions and data hashes. These are operational inference models, not additional evaluated models and not new final-test metrics.

The distinction matters: the prediction pipelines have coefficients learned through 2022/23, while the feature-state snapshot includes completed match results through its `as_of_date` (currently 2026-05-30). Those later results are used only as historical state for a future-date fixture; they do not enter fitted coefficients or model selection. At a prediction date later than the snapshot, all included results precede the requested fixture date. The predictions must not be described as final-test scores or as an independently validated future-season model.

## Team-state storage and feature construction

`src/build_features.py` already accumulates the authoritative project states by calendar date. It now persists its terminal accumulated state to `data/processed/team_state_snapshot.json` after the same-day update cycle. The snapshot stores, for each canonical team key:

- Prior match count, total points, goals for/against, wins and draws.
- Home and away match counts and points.
- Final Elo rating.
- The most recent up-to-five results as points and goal difference.
- One global `as_of_date` and source row count.

This uses the same `team_key` normalization, constants and update order as the historical feature builder; it avoids a second, divergent history implementation. The prediction feature assembler in `src/predict_fixture.py` calls the existing `per_match_summary`, `venue_points` and `recent_summary` functions and computes the two recent-form differences exactly as `build_features.py` does. It selects columns from the unchanged `FEATURE_SETS` in `src/evaluate_models.py` and passes that one-row DataFrame into the chosen fitted pipeline's `predict_proba()`.

The date guard requires `prediction_date > as_of_date`, not `>=`. The project uses a conservative same-calendar-day cutoff, so no result from the snapshot's last date can be treated as known for a fixture on that date. The app also prevents selection of dates before today. If an identity has no state, the feature constructor uses zero prior counts, 1500 Elo, and missing rates/recent averages. The fitted pipeline's median imputer handles missing values using only its training set. The UI reports such a cold start rather than concealing it.

The estimator feature vector excludes team labels, scores, outcome, IDs and fixture date. Inference uses only the selected team's persisted history. The manifest and app verify SHA-256 for each model, the historical feature table and state snapshot; rebuild features and re-export models together when source data changes.

## User interface behavior

`app.py` preserves its nine research sections and adds a tenth `Predict a fixture` section. It loads local joblib pipelines and the JSON state snapshot; it does not retrain on app startup. The form includes home team, away team, model, date and a submit button. On submission the app shows:

- Home win, draw and away win probabilities from scikit-learn `predict_proba()` in fixed H/D/A order.
- The highest-probability class (argmax), clearly distinguished from a guarantee.
- The exact selected model feature values. Missing values are shown as missing with a note that the saved pipeline imputes them.
- The model's training cutoff, state snapshot cutoff, and warning that current 2026/27 results, squad changes, injuries and lineups are absent.
- A warning if either selected team is a cold start.

Team controls are generated from `data/metadata/team_aliases.csv` and names in the historic match data. These identities are known to the project archive, not a current-season registration list. The app does not filter clubs by current UCL qualification or validate fixture existence. It links to UEFA's official fixtures/results page for a human to verify the schedule. The UI accepts a hypothetical manual pairing and date; it cannot certify that fixture.

## Upcoming fixture feed assessment

The official UEFA fixtures/results site and its 2026/27 fixtures article provide current human-readable schedules ([UEFA fixtures/results](https://www.uefa.com/uefachampionsleague/fixtures-results/); [2026/27 schedule](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/)). UEFA's [General Terms and Conditions](https://www.uefa.com/termsconditions/) expressly prohibit automated tools such as robots, spiders or scripts from scraping or collecting site content. The project will not scrape those pages.

OpenFootball's [Champions League repository](https://github.com/openfootball/champions-league) publishes structured Football.TXT data under CC0-1.0 and has proved useful for the historical match archive. At review time its repository tree showed season folders through 2025/26, not a maintained 2026/27 fixture file. It is a promising source to revisit if a current, complete future schedule becomes available in its documented data files; it does not currently guarantee automatic upcoming-fixture updates. No documented public UEFA fixture API with a project-appropriate access policy was identified in the reviewed sources. Therefore the implementation uses a manually selected pair/date and exposes the official UEFA link for human schedule verification.

The current state snapshot ends 2026-05-30, while the current date is 2026-11-17. Consequently, an estimate for the ongoing 2026/27 season cannot use its completed match results or current roster changes. The UI discloses this stale-state limitation. Refreshing the project with future historical results requires a separately validated data update and rebuild; it must preserve timestamp cutoffs.

## Validation and known limits

The tests in `tests/test_prediction_inference.py` check formula parity on a controlled state, cold-start values, same-team rejection, strict date cutoff, feature-column ordering and H/D/A probability reordering. Integration checks load the exported A/B/C pipelines and verify finite probabilities summing to one for a future-date fixture. Each exported A/B/C pipeline reproduces its stored 503 final-test probability rows exactly when fitted on the same 994 final-training rows. Streamlit AppTest checks all ten pages and a submitted manual-fixture form; none of these establishes model accuracy for new fixtures.

Important limitations:

- The operational pipelines are fitted only through 2022/23 by design, so they do not learn more recent result-to-outcome relationships.
- State is updated through 2025/26 only; predictions for 2026/27 are missing current-season results and squad/availability information.
- The model was evaluated historically on 2023/24–2025/26, but the test has historical exposure because C=1 results were viewed before C=.003 selection. This is disclosed elsewhere; the new UI does not repair that limitation.
- Team identity aliases are project heuristics and may merge or separate clubs incorrectly.
- There is no fixture schedule verification or automatic feed.
- Predictions are model estimates from a limited feature set, not guarantees, bookmaker odds or official UEFA probabilities.
- A Streamlit app does not itself meet the original static GitHub Pages deployment requirement. Hosting/deployment remains unperformed and needs a compatible architecture/decision.
