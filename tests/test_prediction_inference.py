import unittest
from datetime import date

import numpy as np

from src.evaluate_models import CLASS_ORDER, FEATURE_SETS
from src.predict_fixture import build_fixture_features, predict_fixture


class FakePipeline:
    classes_ = ["A", "D", "H"]

    def predict_proba(self, frame):
        self.last_columns = list(frame.columns)
        self.last_values = frame.iloc[0].to_dict()
        return np.array([[0.30, 0.20, 0.50]])


class PredictionInferenceTests(unittest.TestCase):
    def setUp(self):
        self.states = {
            "home": {
                "played": 2, "points": 4.0, "goals_for": 3.0, "goals_against": 1.0,
                "wins": 1.0, "draws": 1.0, "home_played": 1, "home_points": 3.0,
                "away_played": 1, "away_points": 1.0, "elo_rating": 1600.0,
                "recent_results": [
                    {"points": 3.0, "goal_difference": 2.0},
                    {"points": 1.0, "goal_difference": 0.0},
                ],
            },
            "away": {
                "played": 1, "points": 0.0, "goals_for": 0.0, "goals_against": 2.0,
                "wins": 0.0, "draws": 0.0, "home_played": 0, "home_points": 0.0,
                "away_played": 1, "away_points": 0.0, "elo_rating": 1500.0,
                "recent_results": [{"points": 0.0, "goal_difference": -2.0}],
            },
        }

    def test_fixture_features_match_expected_state_formulas(self):
        features, cold = build_fixture_features(self.states, "home", "away")
        self.assertAlmostEqual(features["home_points_per_match"], 2.0)
        self.assertAlmostEqual(features["home_goal_diff_per_match"], 1.0)
        self.assertAlmostEqual(features["home_team_home_points_per_match"], 3.0)
        self.assertAlmostEqual(features["away_team_away_points_per_match"], 0.0)
        self.assertAlmostEqual(features["elo_difference"], 160.0)
        self.assertAlmostEqual(features["recent5_points_difference"], 2.0 - 0.0)
        self.assertEqual(cold, {"home": False, "away": False})

    def test_cold_start_retains_missing_rates_and_default_elo(self):
        features, cold = build_fixture_features(self.states, "new-club", "away")
        self.assertTrue(cold["home"])
        self.assertEqual(features["home_prior_matches"], 0.0)
        self.assertTrue(np.isnan(features["home_points_per_match"]))
        self.assertEqual(features["elo_home"], 1500.0)
        self.assertTrue(np.isnan(features["home_recent5_points_per_match"]))

    def test_same_team_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "different"):
            build_fixture_features(self.states, "home", "home")

    def test_historical_or_same_cutoff_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be after"):
            predict_fixture(
                model_name="A", model=FakePipeline(), team_states=self.states,
                home_key="home", away_key="away", prediction_date=date(2026, 5, 30),
                state_as_of_date=date(2026, 5, 30),
            )

    def test_predict_proba_is_reordered_to_h_d_a_and_feature_list_is_exact(self):
        model = FakePipeline()
        result = predict_fixture(
            model_name="Model C", model=model, team_states=self.states,
            home_key="home", away_key="away", prediction_date=date(2026, 6, 1),
            state_as_of_date=date(2026, 5, 30),
        )
        self.assertEqual(model.last_columns, FEATURE_SETS["Model C"])
        self.assertEqual(result["predicted"], "H")
        self.assertEqual(result["probabilities"], {"H": 0.50, "D": 0.20, "A": 0.30})
        self.assertEqual(list(result["probabilities"]), CLASS_ORDER)
        self.assertAlmostEqual(sum(result["probabilities"].values()), 1.0)


if __name__ == "__main__":
    unittest.main()
