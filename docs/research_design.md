# UEFA Champions League Match Outcome Predictor

## Status of the research question

This is a **proposed refinement** of the submitted project proposal and has not been formally resubmitted. The official ES 335 evaluation rubric has now been supplied and is treated as the primary grading source; see docs/rubric_gap_analysis.md for the criterion-by-criterion audit. The separate submitted research proposal is not in the checkout, so a line-by-line comparison to its approved wording is not possible. Against the available project-development brief and rubric, this revision retains the UCL match-prediction task, probabilistic evaluation, chronological leakage controls, and reproducibility priorities. It sharpens the broad modeling objective into incremental feature-group comparisons and adds a player-feature ablation and phase analysis.

> To what extent do historical team performance, Elo-based strength ratings, recent form, and historical player attributes improve the probabilistic prediction of 90-minute UEFA Champions League match outcomes? In particular, do player-level features provide measurable improvements over team-level features, and does predictive performance differ between league-phase and knockout matches?

**Project title remains:** UEFA Champions League Match Outcome Predictor.

## Methodological assessment of the proposed refinement

The refinement is feasible, with several limits to carry into interpretation:

- Historical results begin in 2015/16, so early-season team histories are left-censored. Team statistics and Elo warm up from the available archive rather than from each club’s complete European history.
- The frequency baseline estimates training-period H/D/A priors; this captures the overall home-result frequency but is not a separate, causal estimate of home advantage. Report it as a simple reference model.
- The planned final test spans only three seasons and crosses the 2024/25 format change. Phase comparisons are observational and may reflect different teams, opponents, and rules as well as predictability. Small knockout samples do not support strong comparative claims.
- Rating snapshots and club assignment do not establish a player’s UCL eligibility or match participation. Model D can test squad proxies, but actual-XI claims require dated lineups and a defensible pre-kickoff availability time.
- Published update dates may be day-level rather than timestamped. Use only snapshots strictly earlier than the match date unless a reliable publication time proves the snapshot preceded kickoff; record snapshot age and missingness.
- The original A/B/C ablations estimate feature-group value for regularized Logistic Regression and do not establish universal value across model families. A separate fixed-configuration Random Forest comparison was run on the same validation period; it did not improve on Model C across the primary metrics and did not change selection. The final-test period has prior exposure because C=1 results were viewed earlier; do not use it for further selection or call it historically pristine.
- The supplied development brief also calls for a GitHub Pages website. This research refinement does not replace that deliverable; with limited time, avoid letting the optional player-data branch displace the reproducible baseline and end-to-end project requirements.

## Target and scope

The primary outcome is the match result at the end of regulation time: home win (`H`), draw (`D`), or away win (`A`). Extra-time results and penalties are retained as separate source fields and do not change this label. Aggregate score and team advancement belong to a separate future tournament-simulation component.

## Progressive feature experiments

Use the same initial classifier family across feature variants so that differences mainly reflect the added information. Start with a regularized multinomial Logistic Regression and a training-set class-prior baseline; do not add complex estimators before the pipeline and baseline are stable.

| Variant | Information available before kickoff |
|---|---|
| Baseline | Training-set H/D/A probabilities (and a majority-class reference); the historical home-result rate represents average home advantage. |
| Model A | Historical UCL match results and pre-match cumulative team performance, such as goals for/against and points per prior match. |
| Model B | Model A plus pre-match Elo ratings derived only from earlier 90-minute results. |
| Model C | Model B plus recent form over a predeclared prior-match window. |
| Model D | Model C plus time-safe FIFA/SoFIFA player and squad aggregates; optional if historical coverage and ID/team joins are adequate. |

A separate fixed-configuration Random Forest comparison has also been run as an exploratory validation-only robustness check using the same A/B/C feature groups. It is not part of the frozen model-selection sequence and did not use the final-test data; its results and limitations are documented in [random_forest_validation_experiment.md](random_forest_validation_experiment.md). It did not justify changing the selected models.

For Elo, initialize new teams at a documented common prior, update after each completed match only, and process every match on a calendar date using ratings from before that date. For cumulative and recent features, use only earlier-dated UCL results. This conservative same-day rule avoids needing to infer timezone conversions from local kickoff clocks. Unknown/new teams retain explicit cold-start/missing indicators or the documented prior; do not use future season rankings to fill them.

For Model D, distinguish a dated club-snapshot squad proxy from a match-specific starting XI. Match lineup rows must never be treated as known before kickoff without evidence that the lineup was announced before the assumed prediction time. A player assigned to a club is not assumed to have played or to be registered for that UCL match.

## Chronological evaluation plan

The first evaluation uses this chronological split. The split itself was not chosen from final-test scores, but earlier C=1 final-test results had been inspected; therefore this period is not a historically pristine holdout and is excluded from further selection.

- Development training: 2015/16 through 2020/21.
- Validation: 2021/22 and 2022/23.
- Final chronological test: 2023/24, 2024/25, and 2025/26.
- After feature/model choices are fixed, refit on all seasons through 2022/23 and score the later final-test seasons. This is the chronological reporting period, but it is not historically pristine because earlier C=1 final-test results had been inspected.

The expanded result set currently has 1,497 matches across 11 seasons. All feature variants must be evaluated on the exact same test match rows. For Model D, report coverage and also compute Models A–C on the same Model D-complete subset; do not compare scores from different match populations as though they were directly comparable.

**Primary metrics:** multiclass log loss and multiclass Brier score. Define Brier as the mean over matches of the sum across H/D/A of squared probability error. **Secondary metrics:** accuracy, per-class and macro precision/recall/F1, confusion matrices, and one-vs-rest calibration summaries. Fit scaling, imputation, feature selection, and any tuning on training data only.

## Phase and competition-format analysis

Report sample sizes and results separately for:

1. The pre-2024 group stage.
2. The 2024/25-onward 36-team league phase.
3. Knockout rounds.
4. The new knockout playoffs as their own category where sample size permits.

Do not collapse the old group stage and the new league phase for the main format comparison: before 2024/25, 32 teams played six matches in eight groups; from 2024/25, 36 teams play eight matches against different opponents in a single league table, with a new playoff round for positions 9–24. The change affects opponent mix, match counts, and the competitive meaning of stage-specific comparisons. UEFA documents the new 36-team/144-match league phase and eight matchdays in its [format explanation](https://www.uefa.com/uefachampionsleague/news/0290-1b9c211303c8-e419a4471514-1000/).

Knockout test samples are much smaller than league/group samples. Always show `n`; treat stage-level metric gaps as exploratory and avoid strong claims from small samples. The 2019/20 season used a pandemic-altered schedule and single-match later knockout rounds; it has 119 listed matches instead of the usual 125 and merits a sensitivity note.

## Data and reproducibility state

OpenFootball match results are parsed from preserved raw files. The 2015/16–2025/26 files have been checked against each file's declared match count and observed match-date range; SHA-256 values are recorded in `data/metadata/ucl_source_manifest.csv`. This validates parsing and consistency with source headers, not the completeness of the upstream source against an independent official archive.

The FIFA 15–23 all-updates SoFIFA file is the strongest candidate, but the public male-player CSV is about 5.6 GB and has not been downloaded or audited. The 91 MB legacy file was inspected separately and contains only one snapshot per edition; it has useful annual player IDs and attributes but does not represent all updates. Its IDs are mostly consistent but have a small set of name and birth-date conflicts. See docs/sofifa_research.md for measured coverage and limits. Neither file has been joined to UCL matches. Use the latest valid rating snapshot with a verified publication/update time before kickoff. Where only a calendar date is known, require snapshot date to be strictly earlier than the match date. Do not interpolate from future snapshots. If coverage is incomplete, keep D optional and report the missingness.

## Assessment and open items

The result/Elo/form comparison is feasible with the expanded archive. Model A improved over the class-frequency reference; Elo and recent-form gains were small and not fully consistent. The supplementary fixed-configuration Random Forest validation comparison did not improve Model C on both primary metrics and did not change the selected A/B/C Logistic Regression setup. FIFA/SoFIFA ratings were researched but excluded from all evaluated models: the 5.6 GB all-updates file was not audited, annual snapshots are temporally stale or incomplete for later tests, snapshot club membership is not UCL registration, and complete pre-kickoff lineups are unavailable. Model D is not implemented. No 2026/27 results or automated upcoming-fixture feed are implemented. The historical explorer shows saved retrospective predictions; the separate manual form makes estimates for user-entered scenarios and is not a live fixture service.

Before formal resubmission, compare this wording with the submitted proposal. The local site includes the research narrative, a retrospective historical explorer using saved final-test predictions, and a separate manual fixture estimate form calling saved A/B/C pipelines. The form does not verify the fixture or use current live data. Its team-state snapshot ends 2026-05-30; current 2026/27 results, transfers and roster changes are absent, and no automated upcoming-fixture feed is implemented. Model D remains excluded for the audited data and lineup limitations described above.
