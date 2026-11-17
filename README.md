# UEFA Champions League Match Outcome Predictor

An academic project studying which pre-match information improves probabilistic predictions of UEFA Champions League results. It continues the existing notebooks and environment, with added structured match-data preparation.

## Proposed research direction

The following question is a proposed refinement of the submitted proposal and has not been formally resubmitted:

> To what extent do historical team performance, Elo-based strength ratings, recent form, and historical player attributes improve the probabilistic prediction of 90-minute UEFA Champions League match outcomes? In particular, do player-level features provide measurable improvements over team-level features, and does predictive performance differ between league-phase and knockout matches?

The title remains UEFA Champions League Match Outcome Predictor. The primary target is home win, draw, or away win after 90 minutes. Extra time, penalties, aggregate score and advancement are kept separate for a future tournament-simulation component.

The planned feature sequence is the training-set outcome-frequency baseline; Model A (historical team performance); Model B (A + Elo); Model C (B + recent form); and optional Model D (C + time-safe historical FIFA/SoFIFA features). Model D is not implemented or evaluated. A supplementary one-configuration Random Forest validation comparison is documented separately and did not replace Models A/B/C. Comparisons use common chronological rows and primary metrics of log loss and multiclass Brier score.

## Current data and model status

- Raw OpenFootball UCL match files are preserved in data/raw/.
- 2015/16–2025/26 results parse to data/processed/ucl_matches.csv (1,497 matches).
- Source URLs, hashes, header counts, parsed counts, team counts, and date coverage are in data/metadata/ucl_source_manifest.csv.
- 03_exploratory_analysis.ipynb is an executed descriptive EDA notebook.
- Date-safe feature generation and chronological evaluation for the baseline and Models A–C are implemented. Validation-only draw diagnostics and the selected common C=0.003 configuration are documented; results and probabilities are saved under data/results/. The initial C=1 run is preserved under data/results/initial_c1/.
- A separate, supplementary Random Forest comparison was run only on the established 744-match training / 250-match validation split. It did not use the final-test set and did not alter the frozen A/B/C selection or outputs; see docs/random_forest_validation_experiment.md and reports/random_forest_validation/.
- FIFA/SoFIFA player data was investigated but not joined to matches or included in any evaluated model; Model D has not been implemented or evaluated. The audited FIFA 15–23 legacy file has one snapshot per edition; the 5.6 GB all-updates file was not downloaded or audited, snapshot dates/club assignments do not establish UCL eligibility or lineup participation, and there is no consistent verified contemporaneous coverage across the final-test period. See docs/sofifa_research.md.
- The official ES 335 evaluation rubric has now been supplied and audited in docs/rubric_gap_analysis.md. The separate submitted research proposal is not in the checkout, so its exact wording has not been reconciled.

## Reproduce

From the project root in WSL with Python 3.12:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/parse_football_txt.py
.venv/bin/python src/build_features.py
.venv/bin/python src/diagnose_model_c_draws.py
.venv/bin/python src/evaluate_models.py --logistic-c 0.003
.venv/bin/python src/evaluate_random_forest_validation.py  # optional supplementary validation-only experiment
.venv/bin/python src/export_prediction_models.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/streamlit run app.py
```

The submission website is the static GitHub Pages-compatible site in `docs/`. To refresh its saved evidence and preview it without publishing:

```bash
.venv/bin/python src/build_pages_assets.py
.venv/bin/python src/export_historical_match_centre.py
cp data/exports/historical_match_centre.json docs/site_data/historical_match_centre.json
.venv/bin/python -m http.server 8765 --directory docs
```

Open `http://localhost:8765/`. The site runs the saved A/B/C inference parameters in browser JavaScript; it does not require Streamlit at runtime. See `docs/github_pages.md` for the Pages setup. The verified public repository is https://github.com/raghav-iit/ucl-predictor and is configured as this checkout origin; the project files have not been committed or pushed, and GitHub Pages has not been published. The pinned `requirements.txt` is a full environment snapshot for the notebooks and app, not a minimal runtime list; the current environment passes `pip check`, but a clean reinstall has not been verified.

The parser, feature builder, evaluator, model exporter and static-data exporter regenerate files under `data/processed/`, `data/results/`, `data/models/`, `reports/` and `docs/site_data/`. Reproduce in a fresh project copy or back up the saved submission artifacts first; do not use the frozen submission checkout as a scratch output directory.

See `docs/data_preparation.md` for parsing and coverage; `docs/research_design.md` for the proposed experiment; `docs/model_methodology.md` for feature timing and splits; `docs/model_results.md` for evaluation; `docs/fixture_prediction.md` for manual inference and fixture-source limitations; `docs/project_technical_walkthrough.md` for a code-oriented study guide; `docs/sofifa_research.md` for player-data source findings; `docs/model_c_draw_diagnosis.md` for validation-only diagnosis; `docs/rubric_gap_analysis.md` for criterion-by-criterion evidence; `docs/ai_use_disclosure.md` for AI use; `docs/defense_preparation.md` for student practice; and `docs/references.md` for citations.

## Remaining work

The project retains a Streamlit application and a static GitHub Pages-compatible research site in `docs/`. The historical error explorer displays saved final-test predictions from the frozen evaluation outputs; these are retrospective and not live forecasts. Those historical predictions use match-specific pre-match feature rows, not the latest team-state snapshot. The separate manual fixture form runs saved A/B/C pipelines for a user-entered team/date scenario; only this future-scenario path uses the team-state snapshot ending 2026-05-30, and it does not verify that a fixture is scheduled. Neither path uses live 2026/27 results or an automated upcoming-fixture feed. Current-season results, transfers, roster changes, injuries and lineups are absent. The final-test results had previously been viewed under C=1 and are not a pristine untouched holdout. The site was tested locally but has not been published. FIFA/SoFIFA ratings were investigated but not incorporated; Model D remains unimplemented because player-data dates, coverage, club mappings and lineup evidence are insufficient for a fair time-safe evaluation.

