from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import build_features


class HistoricalFeatureChronologyTests(unittest.TestCase):
    def test_same_date_uses_start_state_and_next_date_uses_completed_results(self):
        # Alpha appears twice on the first date intentionally: this makes the
        # test fail if an earlier same-day result leaks into another fixture.
        matches = pd.DataFrame([
            {
                "season": "2024-25", "date": "2024-09-17", "kickoff_time": "18:45",
                "stage": "League phase", "format_era": "36_team_league_phase",
                "competition_phase": "league_or_group_phase",
                "home_team": "Alpha FC", "away_team": "Beta FC",
                "regulation_home_goals": 2, "regulation_away_goals": 0, "outcome_90m": "H",
                "source_file": "synthetic.txt", "source_line": 1,
            },
            {
                "season": "2024-25", "date": "2024-09-17", "kickoff_time": "21:00",
                "stage": "League phase", "format_era": "36_team_league_phase",
                "competition_phase": "league_or_group_phase",
                "home_team": "Alpha FC", "away_team": "Gamma FC",
                "regulation_home_goals": 1, "regulation_away_goals": 1, "outcome_90m": "D",
                "source_file": "synthetic.txt", "source_line": 2,
            },
            {
                "season": "2024-25", "date": "2024-09-18", "kickoff_time": "18:45",
                "stage": "League phase", "format_era": "36_team_league_phase",
                "competition_phase": "league_or_group_phase",
                "home_team": "Alpha FC", "away_team": "Beta FC",
                "regulation_home_goals": 0, "regulation_away_goals": 1, "outcome_90m": "A",
                "source_file": "synthetic.txt", "source_line": 3,
            },
        ])
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            match_path, feature_path = temp/'matches.csv', temp/'features.csv'
            alias_path, state_path = temp/'aliases.csv', temp/'state.json'
            matches.to_csv(match_path,index=False)
            with patch.object(build_features,'MATCH_PATH',match_path), patch.object(build_features,'FEATURE_PATH',feature_path), patch.object(build_features,'ALIAS_PATH',alias_path), patch.object(build_features,'STATE_SNAPSHOT_PATH',state_path):
                features=build_features.build()
        first_day=features[features.date.eq('2024-09-17')].sort_values('source_line')
        self.assertEqual(len(first_day),2)
        for column in ('home_prior_matches','away_prior_matches','home_recent_matches','away_recent_matches'):
            self.assertEqual(first_day[column].tolist(),[0.0,0.0])
        self.assertEqual(first_day[['elo_home','elo_away']].to_numpy().tolist(),[[1500.0,1500.0],[1500.0,1500.0]])
        next_day=features[features.date.eq('2024-09-18')].iloc[0]
        self.assertEqual(next_day.home_prior_matches,2.0)
        self.assertEqual(next_day.away_prior_matches,1.0)
        self.assertAlmostEqual(next_day.home_points_per_match,2.0)
        self.assertAlmostEqual(next_day.away_points_per_match,0.0)
        self.assertEqual(next_day.home_recent_matches,2.0)
        self.assertEqual(next_day.away_recent_matches,1.0)
        self.assertNotEqual(next_day.elo_difference,build_features.HOME_ADVANTAGE_ELO)


if __name__ == '__main__':
    unittest.main()
