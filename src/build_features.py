from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

from team_identity import team_key

ROOT = Path(__file__).resolve().parents[1]
MATCH_PATH = ROOT / "data" / "processed" / "ucl_matches.csv"
FEATURE_PATH = ROOT / "data" / "processed" / "historical_features.csv"
STATE_SNAPSHOT_PATH = ROOT / "data" / "processed" / "team_state_snapshot.json"
ALIAS_PATH = ROOT / "data" / "metadata" / "team_aliases.csv"

INITIAL_ELO = 1500.0
ELO_K = 24.0
HOME_ADVANTAGE_ELO = 60.0
RECENT_WINDOW = 5


def per_match_summary(state: dict | None, prefix: str) -> dict[str, float]:
    state = state or {}
    played = state.get("played", 0)
    out = {f"{prefix}_prior_matches": float(played)}
    if played:
        out.update({
            f"{prefix}_points_per_match": state["points"] / played,
            f"{prefix}_goals_for_per_match": state["goals_for"] / played,
            f"{prefix}_goals_against_per_match": state["goals_against"] / played,
            f"{prefix}_goal_diff_per_match": (state["goals_for"] - state["goals_against"]) / played,
            f"{prefix}_win_rate": state["wins"] / played,
            f"{prefix}_draw_rate": state["draws"] / played,
        })
    else:
        out.update({
            f"{prefix}_points_per_match": np.nan,
            f"{prefix}_goals_for_per_match": np.nan,
            f"{prefix}_goals_against_per_match": np.nan,
            f"{prefix}_goal_diff_per_match": np.nan,
            f"{prefix}_win_rate": np.nan,
            f"{prefix}_draw_rate": np.nan,
        })
    return out


def venue_points(state: dict | None, venue: str, prefix: str) -> dict[str, float]:
    state = state or {}
    count = state.get(f"{venue}_played", 0)
    points = state.get(f"{venue}_points", 0.0)
    return {
        f"{prefix}_{venue}_prior_matches": float(count),
        f"{prefix}_{venue}_points_per_match": points / count if count else np.nan,
    }


def recent_summary(results: deque, prefix: str) -> dict[str, float]:
    values = list(results)[-RECENT_WINDOW:]
    count = len(values)
    if not count:
        return {
            f"{prefix}_recent_matches": 0.0,
            f"{prefix}_recent5_points_per_match": np.nan,
            f"{prefix}_recent5_goal_diff_per_match": np.nan,
        }
    return {
        f"{prefix}_recent_matches": float(count),
        f"{prefix}_recent5_points_per_match": float(np.mean([x[0] for x in values])),
        f"{prefix}_recent5_goal_diff_per_match": float(np.mean([x[1] for x in values])),
    }


def build() -> pd.DataFrame:
    matches = pd.read_csv(MATCH_PATH, parse_dates=["date"])
    if matches["outcome_90m"].isna().any():
        raise ValueError("90-minute target contains missing labels")
    names = sorted(set(matches.home_team) | set(matches.away_team))
    aliases = pd.DataFrame({"source_name": names, "team_key": [team_key(x) for x in names]})
    if aliases.team_key.isna().any() or aliases.team_key.eq("").any():
        raise ValueError("A source club name normalized to an empty team key")
    aliases.to_csv(ALIAS_PATH, index=False)
    matches["home_key"] = matches.home_team.map(dict(zip(aliases.source_name, aliases.team_key)))
    matches["away_key"] = matches.away_team.map(dict(zip(aliases.source_name, aliases.team_key)))
    matches["match_id"] = matches.source_file.str.replace(".txt", "", regex=False) + ":" + matches.source_line.astype(str)

    team_states: dict[str, dict] = {}
    elo: dict[str, float] = {}
    recent: dict[str, deque] = defaultdict(lambda: deque(maxlen=RECENT_WINDOW))
    output: list[dict] = []

    # All fixtures on one date use start-of-day state; outcomes update state only after all
    # same-date feature rows have been produced.
    for match_date, day in matches.groupby(matches.date.dt.date, sort=True):
        day = day.sort_values(["kickoff_time", "source_file", "source_line"])
        day_rows: list[dict] = []
        elo_updates: dict[str, float] = defaultdict(float)
        result_updates: list[tuple[str, str, float, float, float, float]] = []

        for row in day.itertuples(index=False):
            hkey, akey = row.home_key, row.away_key
            if hkey == akey:
                raise ValueError(f"Same canonical team on both sides: {row.match_id}")

            feature = {
                "match_id": row.match_id,
                "season": row.season,
                "date": row.date.date().isoformat(),
                "stage": row.stage,
                "format_era": row.format_era,
                "competition_phase": row.competition_phase,
                "home_team": row.home_team,
                "away_team": row.away_team,
                "home_key": hkey,
                "away_key": akey,
                "outcome_90m": row.outcome_90m,
                "regulation_home_goals": int(row.regulation_home_goals),
                "regulation_away_goals": int(row.regulation_away_goals),
                "source_file": row.source_file,
                "source_line": int(row.source_line),
            }
            feature.update(per_match_summary(team_states.get(hkey), "home"))
            feature.update(per_match_summary(team_states.get(akey), "away"))
            feature.update(venue_points(team_states.get(hkey), "home", "home_team"))
            feature.update(venue_points(team_states.get(akey), "away", "away_team"))

            home_elo = elo.get(hkey, INITIAL_ELO)
            away_elo = elo.get(akey, INITIAL_ELO)
            feature.update({
                "elo_home": home_elo,
                "elo_away": away_elo,
                "elo_difference": home_elo - away_elo + HOME_ADVANTAGE_ELO,
            })
            feature.update(recent_summary(recent[hkey], "home"))
            feature.update(recent_summary(recent[akey], "away"))
            feature["recent5_points_difference"] = (
                feature["home_recent5_points_per_match"] - feature["away_recent5_points_per_match"]
                if pd.notna(feature["home_recent5_points_per_match"]) and pd.notna(feature["away_recent5_points_per_match"])
                else np.nan
            )
            feature["recent5_goal_diff_difference"] = (
                feature["home_recent5_goal_diff_per_match"] - feature["away_recent5_goal_diff_per_match"]
                if pd.notna(feature["home_recent5_goal_diff_per_match"]) and pd.notna(feature["away_recent5_goal_diff_per_match"])
                else np.nan
            )
            day_rows.append(feature)

            actual = {"H": 1.0, "D": 0.5, "A": 0.0}[row.outcome_90m]
            expected = 1.0 / (1.0 + 10.0 ** (-((home_elo + HOME_ADVANTAGE_ELO) - away_elo) / 400.0))
            change = ELO_K * (actual - expected)
            elo_updates[hkey] += change
            elo_updates[akey] -= change

            home_points = {"H": 3.0, "D": 1.0, "A": 0.0}[row.outcome_90m]
            away_points = {"H": 0.0, "D": 1.0, "A": 3.0}[row.outcome_90m]
            hg, ag = int(row.regulation_home_goals), int(row.regulation_away_goals)
            result_updates.append((hkey, akey, home_points, away_points, hg, ag))

        output.extend(day_rows)
        for hkey, akey, hp, ap, hg, ag in result_updates:
            hs = team_states.setdefault(hkey, {"played": 0, "points": 0.0, "goals_for": 0.0, "goals_against": 0.0, "wins": 0.0, "draws": 0.0, "home_played": 0, "home_points": 0.0, "away_played": 0, "away_points": 0.0})
            a_s = team_states.setdefault(akey, {"played": 0, "points": 0.0, "goals_for": 0.0, "goals_against": 0.0, "wins": 0.0, "draws": 0.0, "home_played": 0, "home_points": 0.0, "away_played": 0, "away_points": 0.0})
            hs["played"] += 1
            hs["points"] += hp
            hs["goals_for"] += hg
            hs["goals_against"] += ag
            hs["wins"] += float(hp == 3)
            hs["draws"] += float(hp == 1)
            hs["home_played"] += 1
            hs["home_points"] += hp
            a_s["played"] += 1
            a_s["points"] += ap
            a_s["goals_for"] += ag
            a_s["goals_against"] += hg
            a_s["wins"] += float(ap == 3)
            a_s["draws"] += float(ap == 1)
            a_s["away_played"] += 1
            a_s["away_points"] += ap
            recent[hkey].append((hp, hg - ag))
            recent[akey].append((ap, ag - hg))
        for key, change in elo_updates.items():
            elo[key] = elo.get(key, INITIAL_ELO) + change

    features = pd.DataFrame(output).sort_values(["date", "match_id"]).reset_index(drop=True)
    if len(features) != len(matches) or features.match_id.duplicated().any():
        raise ValueError("Feature output does not have exactly one row per match")
    score_outcome = np.select(
        [features.regulation_home_goals > features.regulation_away_goals,
         features.regulation_home_goals == features.regulation_away_goals],
        ["H", "D"], default="A",
    )
    if not np.array_equal(score_outcome, features.outcome_90m.to_numpy()):
        raise ValueError("90-minute labels disagree with the parsed regulation-time score")
    features.to_csv(FEATURE_PATH, index=False)
    snapshot = {
        "schema_version": 1,
        "as_of_date": matches.date.max().date().isoformat(),
        "source_rows": int(len(matches)),
        "teams": {},
    }
    for key in sorted(set(aliases.team_key)):
        state = team_states.get(key, {})
        snapshot["teams"][key] = {
            **state,
            "elo_rating": float(elo.get(key, INITIAL_ELO)),
            "recent_results": [
                {"points": float(points), "goal_difference": float(goal_difference)}
                for points, goal_difference in recent[key]
            ],
        }
    STATE_SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(features)} leakage-safe match rows to {FEATURE_PATH}")
    print(f"Wrote {len(snapshot['teams'])} team states as of {snapshot['as_of_date']} to {STATE_SNAPSHOT_PATH}")
    print(f"Team labels: {len(aliases)} source strings -> {aliases.team_key.nunique()} canonical keys")
    print(f"First match cold starts: {int(features.home_prior_matches.eq(0).sum()) + int(features.away_prior_matches.eq(0).sum())} team-sides")
    return features


if __name__ == "__main__":
    build()

