# Publish the static research website

The current submission website is the static site in `docs/`. It is compatible with GitHub Pages and does not run Python in the browser. Manual A/B/C estimates use the saved model parameters and dated team-state snapshot. The retrospective match centre uses the saved final-test predictions and pre-match features; it does not refit models or provide live fixtures.

## Build and preview locally

From the project root in WSL, refresh the model, team-state and research evidence exports and the historical match-centre export, then copy the match-centre file into the Pages data directory:

```bash
.venv/bin/python src/build_pages_assets.py
.venv/bin/python src/export_historical_match_centre.py
cp data/exports/historical_match_centre.json docs/site_data/historical_match_centre.json
.venv/bin/python -m http.server 8765 --directory docs
```

Open `http://localhost:8765/`. The browser must load the page over HTTP because browsers block the JSON `fetch()` requests from a `file://` URL. The Pages site reads `site_data/project.json`, `site_data/historical_match_centre.json`, `site_data/model_parameters.json` and `site_data/team_state.json`. The project manifest is editorial metadata and a rounded presentation of the saved evaluation metrics; the three model, team-state and research-results exports are generated from the backend artifacts. The verified model-parameter and team-state exports are shared unchanged with the existing `docs/site_data` files. The historical fixture file is copied into a separate filename there; the source in `data/exports/` remains untouched.

The export scripts do not fit or select models. Avoid running the model evaluation pipeline in the frozen submission checkout unless intentionally rebuilding research outputs.

## GitHub Pages setup and current status

The published repository is [github.com/raghav-iit/ucl-predictor](https://github.com/raghav-iit/ucl-predictor), with the initial submission commit `932b50a` on `main`. GitHub Pages is configured from `main` → `/docs` and is available at [raghav-iit.github.io/ucl-predictor](https://raghav-iit.github.io/ucl-predictor/). Local changes made after that publication require owner review and a separate push before they appear publicly.

To verify a later update, open repository **Settings → Pages**, confirm `main` and `/docs`, wait for the Actions deployment to pass, then test the public page, navigation, assets, JSON exports, predictor and repository/reference links.

Do not claim that an unpushed local edit is present on the public site.

## Static-hosting behavior and limitations

`index.html`, `styles.css`, `app.js`, `assets/` and `site_data/` are the complete runtime dependencies. Relative paths support the repository subpath used by GitHub Pages. The `.nojekyll` marker preserves the static asset tree. Manual estimates use team history only through 30 May 2026; they are not verified fixtures or live forecasts and do not include 2026/27 results or current-season form. Historical mode is limited to the 503 saved final-test fixtures and their saved Baseline/A/B/C outputs.
