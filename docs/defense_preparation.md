# ES 335 individual defense preparation

**Purpose:** Study aid for the student to personalize and rehearse. This document is not evidence that a defense has been practiced.

## 60-second project explanation

The project compares probabilistic 90-minute home/draw/away predictions using OpenFootball UCL results from 2015/16–2025/26. Historical team features, Elo and recent form use earlier-date results with a conservative same-day cutoff. The frozen comparison is a frequency baseline and regularized multinomial Logistic Regression Models A, B and C. A separate fixed-configuration Random Forest comparison used the same 744/250 chronological train/validation split and A/B/C feature groups. It was supplementary only: no RF variant beat Model C on both primary metrics, so A/B/C remain the project models. The final-test period is chronological but not historically pristine because C=1 test results had been viewed earlier. The selected logistic models never predict a draw as the argmax on final test. FIFA/SoFIFA ratings were researched but not incorporated: update coverage, time alignment, club mapping and lineup evidence were inadequate for a fair Model D evaluation. The historical explorer shows saved retrospective predictions; manual fixture inference is a separate estimate, not a live feed. No 2026/27 results or automated upcoming-fixture feed is implemented.

Rewrite this in your own words and ensure it matches the final project state.

## Walkthrough to practice

1. Open website Overview and explain the question, proposed status and 90-minute target.
2. On Data, explain row meaning, source coverage, validation checks and what those checks do not establish.
3. On Preprocessing, trace one raw score to H/D/A; explain same-date handling, team aliases and training-only imputation/scaling.
4. On Models, explain the baseline and A–C increments; distinguish the supplementary Random Forest check from the selected models.
5. On Evaluation, explain chronological train/validation/final periods, prior C=1 test exposure, and why models share match rows.
6. On Results/Error explorer, inspect a draw and explain actual outcome, predicted probabilities, log loss/Brier implications and limitations.
7. Close with format-change, small-sample, no-lineup and uncertainty limitations.

## Questions likely to be asked

### Problem and target
- What exactly are you predicting, and at what time?
- Why is the target the 90-minute result rather than who advances?
- What does one dataset row represent?
- Which competitions or matches are outside the data?

### Data and preprocessing
- What is the source and how did you validate the parser?
- Why do header-count checks not prove source completeness?
- How are extra time and penalty scores kept from changing the target?
- Why are same-day matches given the same pre-date feature state?
- How are new teams and missing historical rates handled?
- What is the risk of project-derived team aliases?

### Models and evaluation
- Why use a class-frequency baseline?
- What does each feature group add?
- Why use regularized multinomial logistic regression for the frozen A/B/C comparison?
- What was the supplementary Random Forest experiment, and why did it not replace A/B/C?
- Why are log loss and multiclass Brier primary, with accuracy secondary?
- How do chronological periods prevent future information entering past predictions?
- What is the difference between validation and final testing?
- What does calibration tell you that accuracy does not?

### Results and limitations
- Why can the predicted class be wrong when probabilities are informative?
- Why is zero draw argmax a serious limitation?
- What did class weighting do on validation, and why was it rejected?
- Are small A/B/C score differences meaningful without uncertainty estimates?
- Why are phase comparisons cautious after the 2024/25 format change?
- Were FIFA/SoFIFA ratings used in an evaluated model? Why were they excluded?
- Why do FIFA squad ratings not prove a player appeared in a match?
- Does the website provide live 2026/27 predictions or an automatic fixture list? How does the retrospective explorer differ from manual estimates?
- What would you improve next?

## Short answers to the added defense questions

- **Random Forest:** One fixed 500-tree configuration used median imputation, max_features=sqrt, min_samples_leaf=5, seed 335 and no class weighting. It was evaluated only on the existing 250 validation rows for A/B/C feature groups. RF A had the highest macro F1 (0.4204) and correctly predicted one draw, but Model C had lower log loss (0.9491 vs 0.9525) and Brier (0.5599 vs 0.5637), plus higher accuracy. There was no tuning and no change to the frozen selection. Full results are in docs/random_forest_validation_experiment.md.
- **Player ratings:** FIFA/SoFIFA archives were investigated but not joined or evaluated as Model D. The annual file has one snapshot per edition, the 5.6 GB update-history file was not audited, later snapshots do not make a consistent contemporaneous panel, club assignment does not establish UCL registration, and the match data lacks complete time-stamped starting lineups. A squad snapshot would be a proxy, not the actual XI.
- **Website/current season:** The historical explorer displays saved final-test probabilities retrospectively. A separate manual form returns model estimates for a user-entered scenario; it is not a live prediction service and does not verify an official fixture. 2026/27 results and an automated upcoming-fixture feed are not implemented.

## Evidence to know without memorizing

Be ready to locate and explain:
- Match counts and coverage: `data/metadata/ucl_source_manifest.csv`.
- Split row assignments: `data/metadata/evaluation_split_assignments.csv`.
- Feature timing/model definitions: `docs/model_methodology.md`.
- Validation diagnosis/rejected alternatives: `docs/model_c_draw_diagnosis.md`.
- Saved metrics/predictions/config: `data/results/`.
- The app error explorer and one representative example.
- AI-use disclosure: `docs/ai_use_disclosure.md`.

## Student rehearsal checklist

- [ ] I checked AI-use disclosure for completeness and accuracy.
- [ ] I can explain target and one-row meaning without reading.
- [ ] I can trace one feature to its pre-kickoff source.
- [ ] I can explain chronological splitting and train-only preprocessing.
- [ ] I can define log loss and multiclass Brier in plain language.
- [ ] I can describe an improvement and a failure without overstating.
- [ ] I can explain why the supplementary Random Forest result did not replace A/B/C.
- [ ] I can state that player ratings were researched but excluded, and that 2026/27/live fixture data is not implemented.
- [ ] I can explain prior exposure to C=1 test results and why the test must not be tuned further.
- [ ] I personally used the website and can answer questions about its code.
