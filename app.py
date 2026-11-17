from __future__ import annotations

import json
import hashlib
import os
from datetime import date, timedelta
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from src.predict_fixture import predict_fixture

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "data" / "results"
PROCESSED = ROOT / "data" / "processed"
METADATA = ROOT / "data" / "metadata"
FIGURES = ROOT / "reports" / "figures"

st.set_page_config(
    page_title="UEFA Champions League Match Outcome Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

CLASS_ORDER = ["H", "D", "A"]
CLASS_NAMES = {"H": "Home win", "D": "Draw", "A": "Away win"}
MODEL_NAMES = ["Baseline", "Model A", "Model B", "Model C"]
PREDICTION_MODELS = ["Model A", "Model B", "Model C"]


@st.cache_data
def load_data():
    matches = pd.read_csv(PROCESSED / "ucl_matches.csv", parse_dates=["date"])
    metrics = pd.read_csv(RESULTS / "metrics.csv")
    predictions = pd.read_csv(RESULTS / "predictions.csv")
    predictions = predictions[predictions.period.eq("final_test")].copy()
    source = pd.read_csv(METADATA / "ucl_source_manifest.csv")
    splits = pd.read_csv(METADATA / "evaluation_split_assignments.csv", parse_dates=["date"])
    config = json.loads((RESULTS / "model_config.json").read_text())
    old_metrics_path = RESULTS / "initial_c1" / "metrics.csv"
    old_metrics = pd.read_csv(old_metrics_path) if old_metrics_path.exists() else pd.DataFrame()
    figure_path = FIGURES / "calibration_test.png"
    if not all(len(x) for x in [matches, metrics, predictions, source, splits]):
        raise ValueError("One or more required project result files are empty.")
    # Match IDs in predictions use the source filename stem plus source line.
    matches["match_id"] = matches.source_file.str.replace(".txt", "", regex=False) + ":" + matches.source_line.astype(str)
    predictions = predictions.merge(
        matches[["match_id", "home_team", "away_team", "regulation_home_goals", "regulation_away_goals"]],
        on="match_id", how="left", validate="many_to_one",
    )
    predictions["max_probability"] = predictions[["p_H", "p_D", "p_A"]].max(axis=1)
    predictions["error"] = predictions.actual.ne(predictions.predicted)
    return matches, metrics, predictions, source, splits, config, old_metrics, figure_path


@st.cache_resource
def load_prediction_assets(asset_mtimes: tuple[int, int, int]):
    model_dir = ROOT / "data" / "models"
    manifest_path = model_dir / "prediction_model_manifest.json"
    state_path = PROCESSED / "team_state_snapshot.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    feature_path = PROCESSED / "historical_features.csv"
    for path, expected_hash, label in [
        (state_path, manifest["state_snapshot_sha256"], "team-state snapshot"),
        (feature_path, manifest["feature_table_sha256"], "historical feature table"),
    ]:
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"The {label} changed after model export. Re-run src/export_prediction_models.py.")
    models = {}
    for name, details in manifest["models"].items():
        artifact_path = ROOT / details["path"]
        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if actual_hash != details["sha256"]:
            raise ValueError(f"The saved {name} pipeline failed its SHA-256 check.")
        models[name] = joblib.load(artifact_path)
    if snapshot["as_of_date"] != manifest["historical_state_as_of_date"]:
        raise ValueError("Model manifest and team-state snapshot dates do not match.")
    return models, snapshot, manifest


def latest_team_labels(matches: pd.DataFrame) -> dict[str, str]:
    aliases = pd.read_csv(METADATA / "team_aliases.csv")
    source_to_key = dict(zip(aliases.source_name, aliases.team_key))
    appearances = pd.concat([
        matches[["date", "home_team"]].rename(columns={"home_team": "source_name"}),
        matches[["date", "away_team"]].rename(columns={"away_team": "source_name"}),
    ], ignore_index=True)
    appearances["team_key"] = appearances.source_name.map(source_to_key)
    appearances = appearances.dropna(subset=["team_key"]).sort_values("date")
    latest = appearances.groupby("team_key", sort=False).tail(1)
    return dict(zip(latest.team_key, latest.source_name))


try:
    matches, metrics, predictions, source_manifest, split_assignments, model_config, old_metrics, calibration_path = load_data()
except Exception as exc:
    st.error(f"Project outputs could not be loaded: {exc}")
    st.stop()

st.title("UEFA Champions League Match Outcome Predictor")
st.caption("A study of which pre-match information improves probabilistic predictions of 90-minute UCL outcomes.")
st.sidebar.title("Project guide")
page = st.sidebar.radio(
    "Sections",
    [
        "Overview",
        "Data",
        "Preprocessing",
        "Models",
        "Evaluation",
        "Results",
        "Predict a fixture",
        "Error explorer",
        "Limitations",
        "Reproduce & references",
    ],
)
st.sidebar.caption("Primary target: home win, draw, or away win after 90 minutes.")

if page == "Overview":
    st.header("Project overview")
    st.info("The research question below is a proposed refinement of the submitted proposal; it has not been formally resubmitted.")
    st.markdown(
        "> To what extent do historical team performance, Elo-based strength ratings, recent form, "
        "and historical player attributes improve the probabilistic prediction of 90-minute UEFA "
        "Champions League match outcomes? In particular, do player-level features provide measurable "
        "improvements over team-level features, and does predictive performance differ between "
        "league-phase and knockout matches?"
    )
    st.markdown(
        "The project compares progressively richer feature groups. It asks whether the added information "
        "improves the probabilities assigned to home win (H), draw (D), and away win (A). A prediction "
        "is for the score after 90 minutes. Extra time, penalties, aggregate scores, and advancement are "
        "separate tournament-simulation questions."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Parsed matches", f"{len(matches):,}")
    c2.metric("Seasons", matches.season.nunique())
    c3.metric("Final-test matches", int(predictions.match_id.nunique()))
    st.subheader("What is being compared?")
    st.markdown(
        "- **Baseline:** H/D/A frequencies learned from training matches. The overall home-result frequency "
        "captures average home advantage.\n"
        "- **Model A:** historical UCL team performance.\n"
        "- **Model B:** Model A plus Elo strength.\n"
        "- **Model C:** Model B plus recent form.\n"
        "- **Model D:** optional historical FIFA/SoFIFA squad features; not implemented or scored."
    )
    st.markdown(
        "Models A–C use the same regularized multinomial Logistic Regression family and common C value. "
        "The final model setting was selected on validation data. Player features are not assumed useful "
        "unless a future common-match ablation supports that conclusion."
    )

elif page == "Data":
    st.header("Data understanding")
    st.markdown(
        "Each row represents one UEFA Champions League match. The target is the home/draw/away result "
        "after regulation time; extra-time and penalty information are retained separately."
    )
    k = st.columns(5)
    k[0].metric("Seasons", matches.season.nunique())
    k[1].metric("Matches", f"{len(matches):,}")
    k[2].metric("Date range", f"{matches.date.min():%Y}–{matches.date.max():%Y}")
    k[3].metric("Source files", len(source_manifest))
    k[4].metric("Raw size", f"{source_manifest.bytes.sum() / 1024**2:.1f} MiB")
    st.subheader("Coverage and quality")
    coverage = source_manifest[["season", "header_match_count", "parsed_match_count", "parsed_team_count", "bytes", "date_min", "date_max"]].copy()
    coverage["size_mib"] = (coverage["bytes"] / 1024**2).round(2)
    coverage = coverage[["season", "header_match_count", "parsed_match_count", "parsed_team_count", "size_mib", "date_min", "date_max"]]
    coverage.columns = ["Season", "Source header matches", "Parsed rows", "Teams", "Size (MiB)", "First match", "Last match"]
    st.dataframe(coverage, hide_index=True, width="stretch")
    outcome_counts = matches.outcome_90m.value_counts().reindex(CLASS_ORDER, fill_value=0)
    outcomes = pd.DataFrame({"Outcome": [CLASS_NAMES[x] for x in CLASS_ORDER], "Matches": outcome_counts.values}).set_index("Outcome")
    st.subheader("90-minute outcomes across the full descriptive archive")
    st.bar_chart(outcomes)
    st.caption("These full-archive outcome shares are descriptive, not a predictive evaluation. Test scores below use only the held-out chronological period.")
    st.subheader("Key variables")
    st.markdown(
        "- **season, date, kickoff_time, stage:** source match context.\n"
        "- **home_team, away_team:** teams as named in the raw source.\n"
        "- **regulation_home_goals, regulation_away_goals, outcome_90m:** regulation-time score and target.\n"
        "- **listed_final_home_goals / listed_final_away_goals:** extra-time score where listed.\n"
        "- **penalty_home_score / penalty_away_score:** shootout score, never used to redefine the target.\n"
        "- **competition_phase / format_era:** group or league phase, playoff, later knockout, and tournament format."
    )
    st.subheader("Source and access")
    st.markdown(
        "Match results are from the [OpenFootball Champions League repository](https://github.com/openfootball/champions-league), "
        "using the [Football.TXT format](https://openfootball.github.io/spec/). The original raw files are kept in "
        "data/raw/ and SHA-256 hashes and source URLs are recorded in data/metadata/ucl_source_manifest.csv."
    )
    st.warning(
        "Counts are checked against each source file's own header. This verifies parsing consistency, not "
        "independent completeness against UEFA. Qualifying rounds are not included. The archive has 119 "
        "matches in pandemic-altered 2019/20 and 189 matches per season in the 36-team format."
    )
    st.markdown(
        "From 2024/25, the competition changed to a 36-team league phase with eight matches per team and "
        "a new knockout-playoff round. The earlier 32-team group phase and new league phase are shown separately. "
        "[UEFA format explanation](https://www.uefa.com/uefachampionsleague/news/0290-1b9c211303c8-e419a4471514-1000/)."
    )

elif page == "Preprocessing":
    st.header("Preprocessing and feature construction")
    st.subheader("From raw score to target")
    st.markdown(
        "The parser follows Football.TXT score notation. Regulation goals determine H/D/A. AET and penalty "
        "scores are stored in separate columns. If regulation time cannot be resolved from the source record, "
        "the parser stops rather than guessing. Dates without a year are resolved against each source file's "
        "declared date range, including the 2019/20 summer restart."
    )
    st.subheader("Leakage safeguards")
    st.markdown(
        "- Cumulative team statistics, Elo and recent form use only earlier-dated UCL results.\n"
        "- All matches on the same calendar date use the state from the start of that day. Results update "
        "state only after every same-day feature row is created.\n"
        "- Elo updates use the 90-minute H/D/A outcome. Shootout winners do not replace regulation results.\n"
        "- Imputation and standard scaling are fit inside the training-only model pipeline.\n"
        "- Match outcome and score columns are excluded from the model feature lists."
    )
    st.subheader("Feature groups")
    st.markdown(
        "- **A — team performance:** prior points, goals for/against, goal difference, win/draw rates, "
        "home-at-home and away-away points rates.\n"
        "- **B — Elo:** Model A plus pre-match home-minus-away Elo with a documented home adjustment.\n"
        "- **C — recent form:** Model B plus up to five previous UCL matches' points and goal-difference rates.\n"
        "- **D — player attributes:** not implemented. A dated club snapshot would be a squad proxy, not a "
        "confirmed UCL roster or starting XI."
    )
    st.markdown(
        "Team names are normalized through a reviewed project alias map, not an official club ID system. "
        "New teams start from a common Elo prior and have missing historical-rate features until matches accumulate."
    )

elif page == "Models":
    st.header("Baseline and model methodology")
    st.markdown(
        "The frequency baseline predicts H/D/A proportions from the training period. It is a simple reference "
        "that captures the marginal home-result rate, but not team-specific strength."
    )
    model_table = pd.DataFrame([
        {"Model": "Baseline", "Added information": "Training-set H/D/A frequencies"},
        {"Model": "A", "Added information": "Historical team performance before the match"},
        {"Model": "B", "Added information": "A + Elo rating difference"},
        {"Model": "C", "Added information": "B + recent form over up to five prior matches"},
        {"Model": "D", "Added information": "C + dated player/squad aggregates; optional, not yet run"},
    ])
    st.dataframe(model_table, hide_index=True, width="stretch")
    st.markdown(
        "The current estimator is regularized multinomial Logistic Regression, a compact and interpretable probability model for the available sample. The same C=0.003 is used "
        f"for A–C, selected by validation log loss and multiclass Brier. Imputation is median-based and "
        f"scaling is standardization, both fit only on training rows. The exact saved configuration is "
        f"data/results/model_config.json."
    )
    st.caption(
        "This is one interpretable model family, not a claim that logistic regression is universally best. "
        "Model C remains unable to select draws as its top class in the current runs."
    )

elif page == "Evaluation":
    st.header("Evaluation design")
    st.markdown(
        "The evaluation is chronological. Preprocessing is fitted on each training period only. All feature "
        "variants are scored on common matches within each period."
    )
    split_table = pd.DataFrame([
        {"Evaluation role": "Validation training", "Seasons": "2015/16–2020/21", "Matches": int(split_assignments.validation_assignment.eq("train").sum())},
        {"Evaluation role": "Validation", "Seasons": "2021/22–2022/23", "Matches": int(split_assignments.validation_assignment.eq("validation").sum())},
        {"Evaluation role": "Final training", "Seasons": "2015/16–2022/23", "Matches": int(split_assignments.final_assignment.eq("train").sum())},
        {"Evaluation role": "Final test", "Seasons": "2023/24–2025/26", "Matches": int(split_assignments.final_assignment.eq("test").sum())},
    ])
    st.dataframe(split_table, hide_index=True, width="stretch")
    st.markdown(
        "**Primary:** multiclass log loss and multiclass Brier. Both evaluate probability quality and penalize "
        "poor probability assignments; Brier here is the mean across matches of the sum of squared errors "
        "across H/D/A. **Secondary:** accuracy, per-class/macro precision, recall, F1, confusion matrices and "
        "one-vs-rest calibration."
    )
    st.warning(
        "The final C=0.003 configuration was selected on the 250-match validation period, then scored on the "
        "final period. The original C=1 test results had been reported earlier, so the updated final period "
        "is not a pristine unseen test in the strictest historical sense. No later model choices should use it."
    )
    phase_n = predictions[predictions.model.eq("Model C")].groupby(["format_era", "competition_phase"]).size().rename("n").reset_index()
    st.subheader("Final-test phase sample sizes")
    st.dataframe(phase_n, hide_index=True, width="stretch")
    st.caption("Phase comparisons are exploratory. Knockout and playoff samples are small, and the 2024/25 format change also changes opponents and schedule.")

elif page == "Results":
    st.header("Results")
    st.markdown("All figures and tables below load from the saved project result files.")
    overall = metrics[metrics.competition_phase.isna()].copy()
    display = overall[overall.model.isin(MODEL_NAMES)].copy()
    display["model"] = pd.Categorical(display.model, MODEL_NAMES, ordered=True)
    display = display.sort_values(["period", "model"])
    columns = ["period", "model", "n", "log_loss", "multiclass_brier", "accuracy", "precision_macro", "recall_macro", "f1_macro"]
    st.dataframe(display[columns].round(4), hide_index=True, width="stretch")
    st.markdown(
        "Model A improves both primary scores over the frequency baseline. In the final test, Elo slightly "
        "worsens both primary scores relative to A; recent form then yields only a very small improvement "
        "over B. Model A and C are nearly tied on log loss and Brier, while A has the highest accuracy. "
        "No uncertainty interval is available, so do not present these small increments as established gains."
    )
    phase = metrics[metrics.competition_phase.notna() & metrics.model.isin(["Model A", "Model B", "Model C"])].copy()
    phase["phase"] = phase.format_era.str.replace("_", " ") + " / " + phase.competition_phase.str.replace("_", " ")
    phase_display = phase[["phase", "competition_phase", "n", "model", "log_loss", "multiclass_brier"]].copy()
    st.subheader("Final-test scores by phase")
    st.dataframe(phase_display.round(4), hide_index=True, width="stretch")
    if calibration_path.exists():
        st.subheader("Final-test calibration")
        st.image(str(calibration_path), caption="One-vs-rest reliability bins from saved final-test probabilities.")
    st.subheader("Current error pattern")
    st.markdown(
        "Model C's argmax prediction is H=287, D=0, A=216 on the 503-match test; there are 87 actual draws. "
        "Its draw precision, recall and F1 are zero. Its mean H/D/A probabilities are 0.452/0.191/0.357, "
        "versus observed frequencies 0.499/0.173/0.328. Some missed draws receive very high home-win "
        "probability; use the Error explorer below to inspect them."
    )
    with st.expander("Show original C=1 results retained for transparency"):
        if not old_metrics.empty:
            old = old_metrics[old_metrics.competition_phase.isna() & old_metrics.model.isin(MODEL_NAMES)]
            st.dataframe(old[["period", "model", "n", "log_loss", "multiclass_brier", "accuracy", "f1_macro"]].round(4), hide_index=True, width="stretch")
        else:
            st.caption("Original C=1 results archive not found.")

elif page == "Predict a fixture":
    st.header("Predict a manually selected fixture")
    st.markdown(
        "Choose two clubs from the project’s historical team-identity map and a future match date. "
        "The selected saved scikit-learn pipeline constructs probabilities from the selected model’s "
        "pre-match feature group; this is a model estimate, not a guarantee or an official fixture check."
    )
    st.markdown(
        "Verify the actual schedule manually on [UEFA’s official fixtures and results page]"
        "(https://www.uefa.com/uefachampionsleague/fixtures-results/)."
    )
    model_dir = ROOT / "data" / "models"
    required_assets = [
        model_dir / "prediction_model_manifest.json",
        PROCESSED / "team_state_snapshot.json",
    ]
    if not all(path.exists() for path in required_assets):
        st.warning(
            "Prediction assets are not present yet. From the repository root, run "
            "`.venv/bin/python src/build_features.py` and then "
            "`.venv/bin/python src/export_prediction_models.py`. "
            "This does not rerun or change the historical evaluation."
        )
    else:
        try:
            asset_files = [
                model_dir / "prediction_model_manifest.json",
                PROCESSED / "team_state_snapshot.json",
                PROCESSED / "historical_features.csv",
            ]
            asset_mtimes = tuple(path.stat().st_mtime_ns for path in asset_files)
            inference_models, team_state_snapshot, inference_manifest = load_prediction_assets(asset_mtimes)
        except Exception as exc:
            st.error(f"Prediction assets could not be loaded safely: {exc}")
            st.stop()

        state_cutoff = date.fromisoformat(team_state_snapshot["as_of_date"])
        minimum_date = max(date.today(), state_cutoff + timedelta(days=1))
        default_date = minimum_date
        display_names = latest_team_labels(matches)
        team_keys = sorted(
            set(team_state_snapshot["teams"]) & set(display_names),
            key=lambda key: display_names[key].casefold(),
        )
        team_labels = {
            key: f"{display_names[key]} · {key}"
            for key in team_keys
        }

        st.info(
            f"The historical state snapshot ends on {state_cutoff.isoformat()}. "
            "Predictions must be dated later than this cutoff. The snapshot does not include results "
            "or roster changes after that date."
        )
        st.caption(
            f"Inference pipelines use the selected feature lists and C={inference_manifest['selected_logistic_c']} "
            f"fitted on {inference_manifest['training_rows']} matches through "
            f"{inference_manifest['training_cutoff_season']}. Final-test rows used to fit these pipelines: "
            f"{inference_manifest['final_test_rows_used_for_estimator_fit']}. These are separate from the "
            "historical evaluation results shown on the Results page."
        )

        with st.form("manual_fixture_prediction"):
            team_columns = st.columns(2)
            home_key = team_columns[0].selectbox(
                "Home team", team_keys, format_func=lambda key: team_labels[key]
            )
            away_key = team_columns[1].selectbox(
                "Away team", team_keys, index=min(1, len(team_keys) - 1),
                format_func=lambda key: team_labels[key],
            )
            options = ["Model A", "Model B", "Model C"]
            model_name = st.selectbox("Model", options, index=2)
            fixture_date = st.date_input(
                "Prediction date", value=default_date, min_value=minimum_date,
                help="Must be later than the last match date in the available historical-state snapshot.",
            )
            submitted = st.form_submit_button("Generate H/D/A probabilities", type="primary")

        if submitted:
            try:
                prediction = predict_fixture(
                    model_name=model_name,
                    model=inference_models[model_name],
                    team_states=team_state_snapshot["teams"],
                    home_key=home_key,
                    away_key=away_key,
                    prediction_date=fixture_date,
                    state_as_of_date=state_cutoff,
                )
            except Exception as exc:
                st.error(f"Could not generate the prediction: {exc}")
            else:
                if any(prediction["cold_start"].values()):
                    cold_sides = [side for side, cold in prediction["cold_start"].items() if cold]
                    st.warning(
                        "No historical UCL results were available for " + ", ".join(cold_sides) +
                        ". Count features use zero, Elo starts at 1500, and missing rate features "
                        "are imputed with medians learned from the training period."
                    )
                st.subheader(
                    f"{team_labels[home_key]} vs {team_labels[away_key]} · {fixture_date.isoformat()}"
                )
                st.caption(
                    f"{model_name} · team history available through {prediction['state_as_of_date']} · "
                    "model probabilities are estimates, not guarantees."
                )
                probability_columns = st.columns(3)
                for column, label in zip(probability_columns, ["H", "D", "A"]):
                    column.metric(
                        {"H": "Home win", "D": "Draw", "A": "Away win"}[label],
                        f"{prediction['probabilities'][label]:.1%}",
                    )
                predicted_name = {"H": "Home win", "D": "Draw", "A": "Away win"}[prediction["predicted"]]
                st.success(f"Highest estimated probability: {predicted_name}")

                st.subheader("Pre-match inputs used")
                st.markdown(
                    "Values below are the actual feature row sent to the saved pipeline before its "
                    "training-fitted median imputation and scaling. Missing history remains visible as "
                    "missing here; the estimator handles it using its saved training-only imputer."
                )
                feature_table = pd.DataFrame([
                    {
                        "Feature": feature,
                        "Value": value if pd.notna(value) else "Missing (imputed by pipeline)",
                    }
                    for feature, value in prediction["features"].items()
                ])
                st.dataframe(feature_table, hide_index=True, width="stretch")
                with st.expander("How to interpret this estimate"):
                    st.markdown(
                        "- Model A uses cumulative prior UCL performance and venue-specific points rates.\n"
                        "- Model B adds the pre-match Elo difference, including the fixed home adjustment.\n"
                        "- Model C adds points and goal-difference form over up to five prior UCL matches.\n"
                        "- The fitted pipeline was trained through 2022/23; the team-state snapshot uses "
                        f"completed results through {state_cutoff.isoformat()}.\n"
                        "- The project does not verify that these clubs are scheduled to play on this date. "
                        "It has no automatically updated fixture feed.\n"
                        "- The current archive does not include 2026/27 results, injuries, transfers, "
                        "lineups or current-season form. Newer clubs absent from the historical identity "
                        "map cannot be selected."
                    )

elif page == "Error explorer":
    st.header("Explore saved final-test predictions")
    st.markdown(
        "Filter actual out-of-sample predictions, then inspect the probabilities and regulation score for a "
        "selected match. These are historical final-test predictions, not live forecasts."
    )
    d = predictions.copy()
    c = st.columns(5)
    chosen_models = c[0].multiselect("Model", MODEL_NAMES[1:], default=["Model C"])
    chosen_seasons = c[1].multiselect("Season", sorted(d.season.unique()), default=sorted(d.season.unique()))
    chosen_phases = c[2].multiselect("Phase", sorted(d.competition_phase.dropna().unique()), default=sorted(d.competition_phase.dropna().unique()))
    chosen_actual = c[3].multiselect("Actual result", CLASS_ORDER, default=CLASS_ORDER, format_func=lambda x: CLASS_NAMES[x])
    chosen_pred = c[4].multiselect("Predicted result", CLASS_ORDER, default=CLASS_ORDER, format_func=lambda x: CLASS_NAMES[x])
    confidence = st.slider("Minimum maximum-class probability", 0.0, 1.0, 0.0, 0.05)
    filtered = d[
        d.model.isin(chosen_models) & d.season.isin(chosen_seasons) &
        d.competition_phase.isin(chosen_phases) & d.actual.isin(chosen_actual) &
        d.predicted.isin(chosen_pred) & d.max_probability.ge(confidence)
    ].copy()
    filtered = filtered.sort_values("max_probability", ascending=False)
    st.caption(f"{len(filtered)} matching prediction rows")
    if filtered.empty:
        st.info("No rows match these filters.")
    else:
        display = filtered[[
            "season", "date", "home_team", "away_team", "regulation_home_goals", "regulation_away_goals",
            "actual", "predicted", "p_H", "p_D", "p_A", "max_probability", "error", "model",
        ]].copy()
        display = display.rename(columns={
            "season": "Season", "date": "Date", "home_team": "Home", "away_team": "Away",
            "regulation_home_goals": "HG90", "regulation_away_goals": "AG90",
            "actual": "Actual", "predicted": "Predicted", "p_H": "P(H)", "p_D": "P(D)",
            "p_A": "P(A)", "max_probability": "Max probability", "error": "Error", "model": "Model",
        })
        st.dataframe(display.head(100).round(3), hide_index=True, width="stretch")
        ids = filtered.match_id.drop_duplicates().tolist()
        selected = st.selectbox("Inspect a match", ids, format_func=lambda x: (
            filtered.loc[filtered.match_id.eq(x), "date"].iloc[0] + " — " +
            filtered.loc[filtered.match_id.eq(x), "home_team"].iloc[0] + " vs " +
            filtered.loc[filtered.match_id.eq(x), "away_team"].iloc[0] +
            " — " + filtered.loc[filtered.match_id.eq(x), "model"].iloc[0]
        ))
        row = filtered[filtered.match_id.eq(selected)].iloc[0]
        score = f"{int(row.regulation_home_goals)}–{int(row.regulation_away_goals)}" if pd.notna(row.regulation_home_goals) else "score unavailable"
        st.subheader(f"{row.home_team} vs {row.away_team}")
        st.caption(f"{row.date} · {row.season} · {row.competition_phase.replace('_', ' ')} · regulation score {score}")
        probs = st.columns(3)
        for col, label in zip(probs, CLASS_ORDER):
            col.metric(CLASS_NAMES[label], f"{row['p_' + label]:.1%}")
        st.write(f"Actual: **{CLASS_NAMES[row.actual]}** · Predicted: **{CLASS_NAMES[row.predicted]}** · "
                 f"{'Incorrect prediction' if row.error else 'Correct prediction'}")
        if row.actual == "D" and row.error and row.max_probability >= 0.75:
            st.warning("This is a high-confidence missed draw. The current model has zero draw argmax predictions on the final test.")

elif page == "Limitations":
    st.header("Limitations and conclusions")
    st.markdown(
        "- Results begin in 2015/16, so early team-history and Elo features are left-censored.\n"
        "- OpenFootball header counts validate parser consistency, not independent completeness against UEFA.\n"
        "- The date-level same-day rule is conservative; exact kickoff-time availability is not modeled.\n"
        "- Club aliases are project-derived keys, not official IDs.\n"
        "- The selected C=0.003 setting uses a single 250-match validation period; no uncertainty intervals or rolling-origin evaluation are available yet.\n"
        "- Model C still produces no draw argmax predictions and makes some overconfident errors.\n"
        "- Test phase samples for knockouts/playoffs are small; format and opponent mix changed in 2024/25.\n"
        "- No player attributes or actual starting lineups are included. Public squad snapshots are not proof of match participation.\n"
        "- The final test has been evaluated under both the original C=1 and selected C=0.003 configurations; after the update, do not use it to select further changes."
    )
    st.subheader("Conclusion supported by current evidence")
    st.markdown(
        "Historical team-performance features improve probability scores over the class-frequency baseline in "
        "the reported periods. Elo and recent form provide mixed or very small incremental results. The current "
        "evidence does not show that adding features always helps, and it does not establish that phase-specific "
        "predictability differs. Player features remain untested."
    )

elif page == "Reproduce & references":
    st.header("Reproduce and references")
    st.markdown(
        "The raw UCL source files and generated outputs are included in the project checkout. The following "
        "commands run from the repository root in the configured WSL environment:"
    )
    st.code(
        ".venv/bin/python src/parse_football_txt.py\n"
        ".venv/bin/python src/build_features.py\n"
        ".venv/bin/python src/diagnose_model_c_draws.py\n"
        ".venv/bin/python src/evaluate_models.py --logistic-c 0.003\n"
        ".venv/bin/python src/export_prediction_models.py\n"
        ".venv/bin/python -m unittest discover -s tests\n"
        ".venv/bin/streamlit run app.py",
        language="bash",
    )
    st.markdown(
        "Exact match split assignments are in data/metadata/evaluation_split_assignments.csv; the evaluation "
        "configuration is in data/results/model_config.json. Manual-inference model and state provenance are in "
        "data/models/prediction_model_manifest.json and data/processed/team_state_snapshot.json. Historical C=1 "
        "outputs are retained in data/results/initial_c1/. See README.md and docs/ for complete parser, feature, "
        "model, result, fixture-feed and player-data notes."
    )
    st.subheader("Data and method references")
    st.markdown(
        "- [OpenFootball Champions League results](https://github.com/openfootball/champions-league)\n"
        "- [Football.TXT format specification](https://openfootball.github.io/spec/)\n"
        "- [UEFA explanation of the 2024/25 format](https://www.uefa.com/uefachampionsleague/news/0290-1b9c211303c8-e419a4471514-1000/)\n"
        "- [scikit-learn LogisticRegression documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)\n"
        "- [Gneiting & Raftery (2007), strictly proper scoring rules](https://doi.org/10.1198/016214506000001437). Full citations are listed in docs/references.md."
    )
    repository_url = os.getenv("UCL_REPOSITORY_URL")
    if repository_url:
        st.markdown(f"**Project repository:** [{repository_url}]({repository_url})")
    else:
        st.warning(
            "No remote repository URL is configured. This checkout has no Git history, and the app has not "
            "been published or deployed. A repository link must be added after a remote exists and publication is authorized."
        )
    st.subheader("AI-use disclosure")
    st.markdown(
        "OpenAI Codex assisted with repository inspection, research-source review, code and documentation edits, "
        "execution of project scripts, and analysis of generated outputs. Match records and evaluation results "
        "are generated from the cited raw data and code; no results were fabricated. The student must review "
        "the implementation, verify the methods and citations, and be able to explain the project. Add any AI tools "
        "used outside this documented project work before final submission."
    )

