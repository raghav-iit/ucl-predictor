# ES 335 rubric-to-evidence audit

**Audit date:** 2026-11-17
**Project:** UEFA Champions League Match Outcome Predictor
**Authoritative source:** [Official ES 335 project guide](https://ml2026.floodresq.com/project-guide) and the attached Machine Learning Course Portal PDF. The submitted proposal itself is not in this repository, so exact proposal alignment remains unverified.

Status means the requirement is demonstrated by inspectable evidence, not merely that code exists. **Complete** means the available requirement is evidenced; **Partially Complete** means meaningful work exists but a stated gap remains; **Missing** means the required evidence is absent or cannot be established.

## Requirement-by-requirement mapping

| Rubric requirement | Status | Verified evidence | What remains / smallest improvement |
|---|---|---|---|
| **A1. Problem formulation and scope (10):** define the question, prediction target, one row, prediction time and information available | **Partially Complete** | Research question/target and 90-minute scope are in the site’s Question section, README and `docs/research_design.md`. Dataset section now defines a row as a completed main-competition fixture. Feature section states state is pre-date and inputs precede kickoff. | Submitted proposal is absent; proposed refinement has not been formally resubmitted. Add proposal comparison if obtained; otherwise retain the disclosure. |
| **A2. Data understanding (10):** source, size, variables, access limits and quality checks | **Partially Complete** | Site Dataset and README name OpenFootball, 1,497 matches, coverage 2015/16–2025/26, H/D/A counts, row meaning and QC. `docs/data_preparation.md` and `data/metadata/ucl_source_manifest.csv` include parsing, source URLs/hashes, source-declared vs parsed counts and date coverage. | The manifest/source-count checks do not independently audit every result against UEFA. Add a full variable dictionary / sample audit only if time permits; state the upstream completeness limitation. |
| **A3. Preprocessing and statistical reasoning (10):** justify transformations and avoid leakage | **Partially Complete** | `src/parse_football_txt.py`, `src/team_identity.py`, `src/build_features.py`; `docs/data_preparation.md` and `docs/model_methodology.md`. Same-date fixtures share prior-date state; imputer/scaler are in the fitted pipeline. The static site explains these safeguards. | Team aliases are project-derived and history is left-censored. Tests cover date behavior, but a full end-to-end leakage audit and independent preprocessing reproduction have not been demonstrated. |
| **A4. Baseline and method selection (15):** baseline and methods justified for question/data | **Partially Complete** | Training-period class-frequency baseline and controlled A/B/C regularized multinomial Logistic Regression are documented on the site and in `docs/model_methodology.md`. RF is explicitly supplementary and validation-only in `docs/random_forest_validation_experiment.md`. FIFA/SoFIFA was investigated but not used. | Baseline is an outcome-frequency reference, not an explicit home-advantage model. Logistic Regression rationale/assumptions are now stated, but no broad algorithm search is claimed. Model D remains unimplemented due to data quality/temporal limits. |
| **A5. Evaluation design and metrics (20):** fair split, validation vs final test, common samples, justified metrics | **Partially Complete** | Split manifest `data/metadata/evaluation_split_assignments.csv`: train 744 (2015/16–2020/21), validation 250 (2021/22–2022/23), final test 503 (2023/24–2025/26). Metrics/predictions/config in `data/results/`; site and `docs/model_results.md` explain log loss and multiclass Brier as primary, other metrics as secondary, and common rows. | C=1 final-test results were viewed before the later validation selection. The site, README and model-results doc disclose this; it is not a pristine untouched holdout. Only one validation/test window; no uncertainty intervals. Do not tune on the test. |
| **A6. Results, errors and limitations (10):** interpret evidence, inspect errors, disclose limits and avoid overclaim | **Partially Complete** | Site Results includes metric tables, phase slices, calibration plot; Error analysis includes confusion matrix, zero draw recall, RF validation summary and limitations. `docs/model_results.md` has representative high-confidence misses. | No uncertainty intervals; phase subsets n=29 and n=32 are small; final test crosses format regimes. Keep differences descriptive and avoid claiming a phase is more predictable. The site examples do not exhaustively explain causes; no causal explanation is established. |
| **A7. Reproducibility and technical integrity (5):** document sources, data access, split, steps, dependencies, AI use and preserved results | **Partially Complete** | README setup/rebuild commands, requirements, scripts/notebooks, raw data, manifest/hashes, saved split/results/models, citations and `docs/ai_use_disclosure.md`. Existing tests pass in project environment; `pip check` passes. | A clean fresh environment has not been independently installed and run. Rebuild scripts can overwrite derived files; README warns to back up/use a fresh copy. Student should verify commands in a fresh clone before claiming full reproduction. |
| **B1. Interactive website (10):** published GitHub Pages site communicates the complete reasoning and works | **Partially Complete** | Published static site at [raghav-iit.github.io/ucl-predictor](https://raghav-iit.github.io/ucl-predictor/), nine research sections plus predictor, data/results/limitations, links and accessible labels. Repository is public. Browser inspection confirmed data/render and controls. | Published version predates these unpushed documentation/site edits. Narrow-screen visual and keyboard/screen-reader audit is not established. After owner review and push, retest deployment and responsive behavior. |
| **B2. Useful interaction (5):** meaningful visitor interaction | **Complete** | Website offers metric/period comparisons, manual home/away and A/B/C prediction, and historical match lookup with model selection, saved probabilities, actual score/outcome, correctness and pre-match feature context. Historical predictions use saved rows; manual mode is a separate estimate. | No live fixtures/current-season feed by design. Preserve this distinction in labels. |
| **B3. Individual understanding and defense (5):** student can explain and defend implementation | **Partially Complete** | `docs/project_technical_walkthrough.md` and `docs/defense_preparation.md` provide implementation details and likely questions. | Individual understanding cannot be proven by files. Student must rehearse and personally explain target, leakage safeguards, splits, scores, zero draw recall, C=1 exposure and limitations. |

## Additional explicit course requirements

| Requirement | Status | Evidence and gap |
|---|---|---|
| Website sections: question, data, preprocessing, baseline/method, evaluation, results, errors, limitations, conclusion, reproduction | **Partially Complete** | All topics are represented in the static site. Reproduction is concise and links to the repository/docs; a grader should follow the README for full commands. |
| One useful interaction | **Complete** | Model/metric/period controls and working manual/historical predictor. |
| Static GitHub Pages hosting | **Complete for published version** | Public URL is live and static. Streamlit is a separate local/server app; Pages does not run Python. This review's local website changes have not yet been published. |
| References, repository links and AI-use disclosure | **Partially Complete** | Repository and primary references are linked from site; AI disclosure is now linked. Verify the changed site after a reviewed push. |
| Proposal checklist (title, course/student, question, target, source/row/size/access, baseline, method, metric, challenge, interaction) | **Partially Complete** | Public project presentation covers these items, but the exact submitted proposal is absent, so its checklist cannot be reconciled line-by-line. |

## Priority order

1. **Before final submission:** review and push only the approved documentation/site changes; then verify the public Pages build, links, JavaScript data loads and predictor.
2. **High value, moderate effort:** clean-clone installation and smoke reproduction of parsing/tests without overwriting frozen outputs; document any dependency or command issue.
3. **High value, low effort:** student defense rehearsal, especially the draw failure and test-exposure caveat.
4. **Optional:** keyboard and narrow-viewport review; add variable dictionary and uncertainty analysis only if time permits. Do not conduct further model selection on final test.

## Risks that could cost marks

- Treating the final test as untouched despite prior C=1 inspection.
- Calling tiny A/B/C score differences meaningful or generalizing phase gaps from small knockout samples.
- Failing to explain zero draw recall or showing accuracy alone.
- Describing Model D/player ratings or 2026/27 live fixtures as implemented.
- Rebuilding in place and overwriting frozen artifacts.
- Publishing documentation changes before public-site verification.
- Being unable to explain the feature formulas, prediction-time boundary, score parsing or model comparison independently.
