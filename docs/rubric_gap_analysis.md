# ES 335 rubric-to-evidence gap analysis

**Initial audit date:** 2026-11-16  
**Submission-readiness recheck:** 2026-11-17
**Project:** UEFA Champions League Match Outcome Predictor  
**Authority:** Official ES 335 rubric and professor submission instructions supplied by the user.  
**Scope:** The submitted proposal is not present in the checkout, so exact alignment with its approved wording cannot be verified. The revised research question remains a proposed change.

## Status definitions

- **Implemented and verified:** an artifact exists and a relevant run/check or content inspection was completed.
- **Implemented, explanation/evidence incomplete:** code or an artifact exists, but grader-facing explanation or independent verification is inadequate.
- **Missing:** no current artifact demonstrates the requirement.
- Website evidence and repository reproducibility evidence are assessed separately.

## Executive assessment

The core pipeline covers 11 seasons (2015/16–2025/26) and 1,497 parsed matches. It includes executed EDA, date-safe A/B/C feature construction, chronological evaluation, saved results and a validation-only investigation of Model C's zero-draw argmax. The Streamlit app preserves its nine research sections and historical error explorer, and now adds manual fixture inference from saved A/B/C pipelines and a dated team-state snapshot. All ten sections and a submitted prediction form passed Streamlit AppTest smoke checks.

The project is **not submission-complete**. Uncertainty analysis, automated leakage checks, stronger source-version provenance, independent match-level source validation, defense preparation, and manual browser QA remain open. There is no Git repository or remote, so a repository link cannot yet be shown. Do not publish or deploy without authorization.

The final test needs a qualification: C=1 test results had been inspected before C=0.003 was selected from validation. The new C=0.003 run did not drive another selection, but the test is not pristine in the strict historical sense. Do not tune further on it.

## A. Shared ML reasoning — 80 points

| Criterion | Status | Evidence already verified | Partial / missing / evidence still needed |
|---|---|---|---|
| **1. Problem formulation and scope — 10** | **Implemented; proposal alignment incomplete** | `README.md`, `docs/research_design.md`, and app Overview state the retained title, proposed research question and H/D/A 90-minute target. Parsing/data docs distinguish regulation result from extra time, penalties and advancement. | Proposal is absent and revised wording was not formally resubmitted. Explicitly state coverage/exclusions and prediction time. Final evidence: proposal comparison if supplied, plus concise scope on the site. |
| **2. Data understanding — 10** | **Implemented; independent validation partial** | `03_exploratory_analysis.ipynb` is executed. `docs/data_preparation.md` explains row meaning, source, parse/coverage checks and format change. `data/metadata/ucl_source_manifest.csv` records URLs, hashes, bytes, dates and declared/parsed counts. App Data page displays source, coverage, fields and caveats. | Header-count agreement is not an independent official match audit. Full variable dictionary and source revision pin are absent; ambiguous records need clearer evidence. Add dictionary and retrieval/version/access notes; audit a sample independently or state limitation. |
| **3. Preprocessing and statistical reasoning — 10** | **Implemented; broader leakage checks still missing** | `src/parse_football_txt.py`, `src/team_identity.py`, `src/build_features.py`, `src/evaluate_models.py`, and `docs/model_methodology.md` show score parsing, alias handling, date-ordered features, same-date start state and training-only imputation/scaling. `tests/test_prediction_inference.py` checks prediction-time feature formulas and date guards. | Existing tests do not prove every historical feature uses no future result or that all training transforms are fit only on training data. Histories are left-censored at 2015/16; aliases are project-derived. Add full pipeline assertions and a variable dictionary. |
| **4. Baseline and method selection — 15** | **Implemented; rationale/sensitivity partial** | src/evaluate_models.py implements the training H/D/A frequency baseline and regularized multinomial Logistic Regression Models A/B/C; data/results/model_config.json records settings. A one-configuration Random Forest comparison on the same 744/250 validation split is documented separately and did not establish an overall improvement or change model selection. | Class prior is not a separately estimated home-advantage effect. No RF hyperparameter search was performed. Model D remains unjoined/unevaluated because player coverage, temporal alignment and lineup evidence are inadequate. Explain limits; keep D optional absent defensible coverage. |
| **5. Evaluation design and metrics — 20** | **Chronological evaluation implemented; uncertainty incomplete** | `data/metadata/evaluation_split_assignments.csv` gives match-level assignments; counts are 744 train / 250 validation / 503 final test, with common rows for baseline/A–C. `data/results/metrics.csv`, predictions, confusion matrices, calibration bins and config exist. Results docs define primary scores and phase counts. | Only one validation and final window; no uncertainty intervals or rolling-origin robustness. Old knockout n=29 and new playoff n=32. C=1 test results were seen before C=.003 selection, so this is not historically untouched. Add dependence-aware uncertainty or limit claims; never select on this test. |
| **6. Results, errors, limitations — 10** | **Error diagnosis implemented; uncertainty incomplete** | `docs/model_c_draw_diagnosis.md` reports validation-only probabilities, imbalance, calibration, feature distributions/correlations, A/B/C, regularization and class weighting. `docs/model_results.md` reports metrics, class failures, representative errors and phase limits. Saved diagnostic CSVs and predictions support the claims. | A/B/C still have zero draw argmax on final; confident draw misses remain. No uncertainty intervals. Ensure errors/calibration are legible on site and do not imply small metric differences are meaningful. |
| **7. Reproducibility and technical integrity — 5** | **Core artifacts present; closure partial** | Code/notebooks, raw inputs, hashes, requirements, split manifest, predictions/metrics/config, `docs/ai_use_disclosure.md`, `docs/references.md`, and README commands exist. The selected evaluator reproduced byte-identical metrics, predictions and split assignments. | No `.git` or remote. README commands now include clean environment setup, but a clean environment has not yet been rebuilt. No automated regression checks; citations/access need review. Verify full parse/build/evaluation reproduction and artifact links; back up before any separately authorized Git setup. |
| **B1. Interactive website — 10** | **Implemented and smoke-verified locally; visual QA/deployment/link incomplete** | Root `app.py` has ten sections: the nine research sections plus `Predict a fixture`. The new page loads saved sklearn A/B/C pipelines, checks artifact hashes, accepts manual teams/model/date and displays `predict_proba()` H/D/A probabilities and inputs. All ten rendered; a submitted fixture produced probabilities without exceptions. | AppTest does not prove visual quality, accessibility or deployment. There is no automatic fixture verification/feed. GitHub Pages deployment is incompatible with this Streamlit server app; no repository remote exists. Manually inspect layout and links; hosting architecture remains open. |
| **B2. Useful interaction — 5** | **Implemented and functionally smoke-verified locally** | Visitors can request A/B/C inference for a manual fixture and inspect the input features; the historical explorer separately filters held-out predictions and match details. A submitted form displayed three probabilities. | Fixture existence is not verified against an official schedule. Test tools do not establish visitor usefulness/accessibility. Manually inspect cold-start/stale-state disclosures and historical filters. |
| **B3. Individual understanding and defense — 5** | **Missing as a deliverable** | Docs/notebooks offer study material; AI disclosure exists. | No defense guide or evidence of rehearsal. Create a guide/question bank; student must personalize and practice explanations. |

## Professor's website-only narrative checklist

The grader must understand and assess the project from the website alone. Repository material does not substitute for this narrative.

| Website requirement | Status | Evidence / remaining work |
|---|---|---|
| Question and meaning of one row | **Implemented and AppTest-verified** | Overview/Data state proposed question, 90-minute target and match row meaning; visually review. |
| Sources, size, variables, quality | **Implemented; explanation review needed** | Data page uses source manifest/data; verify table ordering, citations, quality caveats and access limitations. |
| Preprocessing and rationale | **Implemented and AppTest-verified** | Preprocessing page explains parser, same-date cutoff, features and train-only transforms; check against code. |
| Baseline and models | **Implemented and AppTest-verified** | Models page explains baseline/A–D; ensure D is clearly optional/unrun. |
| Splits and metrics | **Implemented; visual QA needed** | Evaluation page reads split/config/metrics; confirm counts and primary metric rationale. |
| Results and error analysis | **Implemented from saved outputs; visual QA needed** | Results/Error explorer use saved predictions, metrics and calibration; confirm draw failure/sample sizes visible. |
| Limitations | **Implemented and AppTest-verified** | Limitations page covers format change, small phase samples, absent lineups and uncertainty; audit claim consistency. |
| Useful interaction | **Implemented and functionally AppTest-verified** | Manual team/model/date form invokes fitted A/B/C `predict_proba()`; historical explorer remains. Fixture schedule is not verified. |
| Repository link/technical details | **Partial** | Reproduction/references page gives local instructions and citations. Public repository link is missing because no remote exists. |

## Repository independent-reproduction checklist

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Code and notebooks | **Implemented** | `src/`, notebooks 01–03; describe safe rerun status. |
| Exact preprocessing | **Implemented; explanation partial** | Parser/feature/evaluator and methodology; add dictionary and leakage checks. |
| Exact split assignments | **Implemented and verified** | `data/metadata/evaluation_split_assignments.csv`; retain in final bundle and document counts. |
| Full results/experiments | **A–C and diagnosis implemented; uncertainty incomplete** | `data/results/`, `initial_c1/`, validation diagnostics; add uncertainty/sensitivity only if defensible. |
| Config/preprocessing parameters | **Implemented; explanation partial** | `data/results/model_config.json`, pipeline and methodology; verify against rerun. |
| Data citations/access | **Partial** | `docs/references.md`, `docs/data_preparation.md`, manifest; add retrieval/revision and attribution notes where known. |
| README setup/run | **Implemented; clean setup still unverified** | README now gives Python 3.12 venv/install, run order and app launch. A rerun of the evaluator reproduced saved metrics, predictions and split file hashes. Rebuild from a clean environment and verify data-access instructions/output paths. |
| AI-use disclosure | **Implemented; student confirmation needed** | `docs/ai_use_disclosure.md`; student confirms completeness and independent review. |
| Citations/references | **Implemented; audit needed** | `docs/references.md` and in-app citations; verify support and website visibility. |
| Version control | **Missing** | WSL reports not a Git repository. No init/commit/push occurred. Back up first; request authorization before initialization or publishing. |

## Ranked remaining work

| Rank | Task | Expected rubric impact | Effort | Completion evidence |
|---:|---|---|---|---|
| 1 | Run a clean-environment reproduction and verify inference asset rebuild/hashes | High: evaluation (20), reproducibility (5) | Medium | Successful clean setup plus stable evaluation files and exported model/state manifests. |
| 2 | Browser QA all app pages and interactions, including prediction cold start/stale-state wording | High: website (10) + interaction (5) | Low–medium | Manual review of layout, links, prediction form, filters and empty states. |
| 3 | Create defense guide and student walkthrough | Direct: 5 | Low | Guide plus student-personalized practice; agent cannot claim rehearsal. |
| 4 | Add leakage/data assertions and variable dictionary | High: preprocessing (10), data (10), reproducibility | Medium | Checks for labels, chronology, same-date state and training-only transforms. |
| 5 | Estimate uncertainty/robustness for model comparisons | High: evaluation (20), results (10) | Medium–high | Dependence-aware analysis or candid limitation; no test-based selection. |
| 6 | Complete provenance/access and repository-link strategy | Moderate: data (10), reproducibility (5), website | Low–medium | Source version/access/attribution; no Git/deploy without permission. |
| 7 | Optional FIFA/SoFIFA Model D | Supports scope; high effort | High | Only after core deliverables; dated snapshots, valid joins, common-row comparison. |

## Recommended next milestone

**Website review and leakage/data checks.** The prediction page now runs locally from saved pipelines and state. Next visually inspect all ten sections, manually verify filter/prediction interactions and cold-start/stale-state wording; then add full-pipeline leakage checks and a feature dictionary. Follow with clean-environment reproduction and student-personalized defense practice. Keep Model D deferred.

## Risks with substantial mark impact

1. A running but unclear website can lose most website points; AppTest is not visual/content review.
2. The original brief specifies GitHub Pages, while genuine scikit-learn inference in the current Streamlit app needs a Python app host. No deployment architecture has been selected or published.
3. A clean-environment setup has not yet been tested end to end.
4. C=1 test results were seen before choosing C=.003. Updated scores are reporting-only after selection but the test is not historically untouched; do not tune further.
5. Zero draw argmax and confident draw misses need candid discussion; accuracy hides this weakness.
6. Small phase samples and the 2024/25 format change prohibit broad phase claims.
7. No Git remote means no verifiable repository link. Do not initialize or publish without authorization.
8. Missing uncertainty weakens claims about small score differences.

## Validation performed before static-site work

- Inspected current docs, outputs, split manifest, app and repository state.
- Confirmed no `.git` directory.
- Re-ran the parser (1,497 rows from 11 files), feature builder, and evaluator; raw input hashes were unchanged and metrics, predictions, and split-manifest hashes were byte-identical after regeneration.
- Confirmed `data/results/model_config.json` parses as valid JSON.
- Ran five inference unit tests: feature calculations, cold-start handling, date cutoff, same-team rejection and probability class ordering.
- Fit and loaded all three inference pipelines using 994 training rows; confirmed zero final-test fit rows and 503 final-test rows excluded.
- Confirmed raw input and all historical evaluation output hashes were unchanged by state/model export.
- Ran Streamlit AppTest for all ten navigation sections and submitted a manual fixture form; each completed without exception.
- Did not publish, deploy, initialize Git, or claim student rehearsal.

## Deadline recheck: static GitHub Pages site and remaining status

The prior tables above record the earlier Streamlit-only state. This dated recheck supersedes their website status where noted. No claims below mean that the site has been published: this checkout still has no `.git` directory, remote, or verified repository URL, and no push/deployment was performed.

| Criterion | Recheck status | Evidence from this recheck | Still incomplete |
|---|---|---|---|
| A1 Problem formulation | **PARTIAL** | Static site Overview states proposed question, target and scope; not formally resubmitted. | Submitted proposal absent for exact reconciliation. |
| A2 Data understanding | **PARTIAL** | Static site reads actual 1,497-row/11-season coverage and source manifest; source counts/date ranges/hashes are rendered. | Independent official match audit and source revision pin absent. |
| A3 Preprocessing/statistical reasoning | **PARTIAL** | Website documents regulation target, alias limitations, as-of-date ordering and training-fitted imputation/scaling; five inference tests pass. | Exhaustive property checks across every generated historical feature still absent. |
| A4 Baseline/method | **PARTIAL** | Website explains the frequency baseline and A/B/C incremental features, common regularized Logistic Regression and validation-selected C. The supplementary fixed-configuration Random Forest comparison is reported in repository documentation. | RF did not establish an overall gain and was not added to the website inference choices; no uncertainty analysis. Model D correctly remains not implemented. |
| A5 Evaluation/metrics | **PARTIAL** | Website shows counts (744 train, 250 validation, 994 final-fit, 503 final test), saved log loss/Brier and secondary metrics, split logic and common test comparisons. | One validation/test window only; no uncertainty estimates. Final test is historically compromised by prior C=1 viewing, explicitly disclosed. |
| A6 Results/errors/limitations | **PARTIAL** | Website renders saved metrics, calibration figure, selectable confusion matrix and filters over actual held-out errors; draw failure and 87 missed draws shown. | No intervals; representative errors do not establish causal diagnoses. Keep claims appropriately tentative. |
| A7 Reproducibility/integrity | **PARTIAL** | README and `docs/github_pages.md` describe local static-site build/preview and Pages configuration. The exporter hash-checks its model/state inputs and only reads original results. Five unit tests pass; dependency consistency check passes. | Full clean reinstall/reproduction remains unverified. Git remote/repository URL and actual Pages publication remain unavailable. |
| B1 Interactive website | **PARTIAL (local pass; publication pending)** | `docs/index.html` is a static site with all nine research sections plus prediction. The browser loaded data, tables, confusion matrix, calibration image and prediction controls; no external server needed by the static app. | Not deployed; no verified repository URL. Static browser interaction was exercised locally only. |
| B2 Useful interaction | **PASS locally; PARTIAL as submission evidence** | Manual team/model/date form generated H/D/A probabilities and displayed 27 pre-match features. Model C example output matched Python `predict_proba()` (browser rounded 40.0/24.1/35.9%; Python 39.9658/24.1075/35.9267%). | Official fixture checking is not offered. Grader-facing live site cannot be checked until owner publishes it. |
| B3 Individual understanding/defense | **PARTIAL** | `docs/defense_preparation.md`, full technical walkthrough and AI-use disclosure are present. | Student must personally verify disclosure, study and rehearse; no rehearsal evidence can be supplied by this audit. |

### Website interaction checks completed

- Opened the static site using a local HTTP server and confirmed browser-rendered content and data exports load.
- Confirmed the source manifest table, chronological split counts, saved validation/final-test metric table, confusion matrix, calibration figure, error explorer, and all nine research sections appear in the rendered document.
- Submitted the manual fixture form for 1. FC Union Berlin vs 1899 Hoffenheim on 2026-11-17 for A, B and C. Browser displayed A 39.6% / 24.0% / 36.4%, B 40.5% / 23.9% / 35.6%, and C 40.0% / 24.1% / 35.9% (H/D/A). Direct Python calls to each saved pipeline returned respectively (39.5578%, 24.0232%, 36.4190%), (40.5045%, 23.8849%, 35.6107%), and (39.9658%, 24.1075%, 35.9267%). These match the browser values to one decimal place; each probability vector sums to 1 before display rounding.
- `src/build_pages_assets.py` ran successfully; it checked model, feature-table and team-state hashes against the inference manifest. It did not fit models or rewrite saved evaluation files.
- `python -m unittest discover -s tests -v`: five tests passed. `python -m pip check`: no broken requirements.
- GitHub Pages readiness is implemented as static files under `docs/` with relative asset paths, `.nojekyll`, and setup instructions. Actual publishing, remote URL verification, clean-environment recreation, and broad visual/accessibility QA remain incomplete.

### Highest remaining mark risks

1. **Deployment evidence:** the local static website now addresses GitHub Pages technically, but the project owner must put it in the actual submission repository and publish it. There is no verified repo URL in this checkout, and publishing is intentionally not performed.
2. **Evaluation caveat:** the test window was viewed under a prior C=1 model before C=0.003 was selected using validation. Clearly label the scores and do not tune on them further.
3. **Metric uncertainty and format change:** one chronological test window, no intervals, small knockout subsets, and a 2024/25 format change restrict claims.
4. **Draw performance:** selected classifiers predict no final-test draws by argmax; the site shows this directly. It is a major model limitation, not something to hide.
5. **Reproduction:** dependencies currently pass `pip check`, but no clean environment was created tonight. If setup time permits, do a fresh installation only in a disposable environment and compare saved outputs without replacing originals.
6. **Defense:** reading the guide is not equivalent to individual understanding; the student should rehearse and be able to explain the test-set caveat without overstating the results.
