from __future__ import annotations

import re
from hashlib import sha256
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATE_RE = re.compile(r"(?:\w{3}\s+)?(\w{3})\s+(\d{1,2})(?:\s+(\d{4}))?$")
DATE_RANGE_RE = re.compile(
    r"^# Date\s+\w{3}\s+(\w{3})\s+(\d{1,2})\s+(\d{4})\s+-\s+"
    r"\w{3}\s+(\w{3})\s+(\d{1,2})\s+(\d{4})",
    re.M,
)
TIME_RE = re.compile(r"^(\d{2}:\d{2})\s+(.+)$")
MATCH_RE = re.compile(
    r"^(?P<home>.+?)\s+v\s+(?P<away>.+?)\s+(?P<score>\d+\s*-\s*\d+.*)$"
)
SCORE_RE = re.compile(r"(\d+)\s*-\s*(\d+)")


def parse_file(path: Path) -> list[dict]:
    season = path.stem.removeprefix("ucl_")
    season_start = int(season[:4])
    source_text = path.read_text(encoding="utf-8")
    date_range = DATE_RANGE_RE.search(source_text)
    if date_range:
        sm, sd, sy, em, ed, ey = date_range.groups()
        source_start = date(int(sy), pd.to_datetime(sm, format="%b").month, int(sd))
        source_end = date(int(ey), pd.to_datetime(em, format="%b").month, int(ed))
    else:
        source_start = date(season_start, 7, 1)
        source_end = date(season_start + 1, 6, 30)
    current_date: date | None = None
    current_month: int | None = None
    current_stage = "Unknown"
    current_time: str | None = None
    rows: list[dict] = []
    errors: list[tuple[int, str]] = []

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("="):
            continue
        if line.startswith("▪"):
            current_stage = line[1:].strip()
            current_time = None
            continue
        dm = DATE_RE.fullmatch(line)
        if dm:
            month_name, day, year = dm.groups()
            month = pd.to_datetime(month_name, format="%b").month
            if year:
                current_date = date(int(year), month, int(day))
            else:
                candidates = [
                    date(y, month, int(day))
                    for y in sorted({source_start.year, source_end.year})
                    if source_start <= date(y, month, int(day)) <= source_end
                ]
                if len(candidates) == 1:
                    current_date = candidates[0]
                elif candidates:
                    current_date = candidates[0]
                else:
                    y = season_start if month >= 7 else season_start + 1
                    current_date = date(y, month, int(day))
            current_month = month
            current_time = None
            continue

        time_match = TIME_RE.match(line)
        if time_match:
            current_time, line = time_match.groups()
        mm = MATCH_RE.match(line)
        if not mm:
            continue
        if current_date is None:
            errors.append((line_no, "match before a date"))
            continue

        home, away, score_text = mm.group("home", "away", "score")
        # Football.TXT lists the shoot-out score before the after-extra-time score.
        # For AET records its first parenthetical score is the regulation-time result;
        # this follows the source's documented fuller breakdown convention.
        aet = bool(re.search(r"a\.?e\.?t\.?", score_text, re.I))
        penalties = bool(re.search(r"pen\.?", score_text, re.I))
        groups = SCORE_RE.findall(score_text)
        if not groups:
            errors.append((line_no, "unreadable score"))
            continue

        if penalties:
            shootout = tuple(map(int, groups[0]))
            aet_pos = re.search(r"a\.?e\.?t\.?", score_text, re.I)
            aet_score = tuple(map(int, SCORE_RE.search(score_text[aet_pos.end():]).groups())) if aet_pos and SCORE_RE.search(score_text[aet_pos.end():]) else None
            if aet and len(groups) >= 4:
                regulation = tuple(map(int, groups[2]))
            elif aet and aet_score == (0, 0):
                # A 0-0 AET score means neither regulation time nor extra time had goals.
                regulation = (0, 0)
            else:
                regulation = None
        elif aet:
            aet_score = tuple(map(int, groups[0]))
            shootout = None
            # The documented notation is: AET result (regulation result, half-time result).
            if len(groups) >= 3:
                regulation = tuple(map(int, groups[1]))
            elif aet_score == (0, 0):
                regulation = (0, 0)
            else:
                regulation = None
        else:
            aet_score = None
            shootout = None
            regulation = tuple(map(int, groups[0]))

        final_score = tuple(map(int, groups[0])) if not penalties else None
        if regulation is None:
            outcome = None
            hg90 = ag90 = None
        else:
            hg90, ag90 = regulation
            outcome = "H" if hg90 > ag90 else "A" if hg90 < ag90 else "D"
        rows.append({
            "season": season,
            "date": current_date.isoformat(),
            "kickoff_time": current_time,
            "stage": current_stage,
            "home_team": home.strip(),
            "away_team": away.strip(),
            "regulation_home_goals": hg90,
            "regulation_away_goals": ag90,
            "outcome_90m": outcome,
            "listed_final_home_goals": final_score[0] if final_score else (aet_score[0] if aet_score else None),
            "listed_final_away_goals": final_score[1] if final_score else (aet_score[1] if aet_score else None),
            "penalty_home_score": shootout[0] if shootout else None,
            "penalty_away_score": shootout[1] if shootout else None,
            "is_extra_time": aet,
            "is_penalty_shootout": penalties,
            "competition_phase": (
                "league_or_group_phase" if re.search(r"group|gruppe|league", current_stage, re.I)
                else "knockout_playoff" if re.search(r"play.?off", current_stage, re.I)
                else "knockout" if re.search(r"final|round|quarter|semi", current_stage, re.I)
                else "unknown"
            ),
            "format_era": "36_team_league_phase" if season_start >= 2024 else "32_team_group_stage",
            "source_file": path.name,
            "source_line": line_no,
        })
    if errors:
        raise ValueError(f"{path.name}: unparsed match records: {errors[:10]}")
    outside = [r for r in rows if not source_start.isoformat() <= r["date"] <= source_end.isoformat()]
    if outside:
        raise ValueError(f"{path.name}: dates outside source header range: {outside[:3]}")
    return rows


def main() -> None:
    files = sorted(RAW_DIR.glob("ucl_*.txt"))
    if not files:
        raise FileNotFoundError(f"No ucl_*.txt files under {RAW_DIR}")
    all_rows: list[dict] = []
    manifest: list[dict] = []
    for path in files:
        rows = parse_file(path)
        header = path.read_text(encoding="utf-8")
        declared = re.search(r"^# Matches\s+(\d+)", header, re.M)
        expected = int(declared.group(1)) if declared else None
        if expected is not None and len(rows) != expected:
            raise ValueError(f"{path.name}: parsed {len(rows)} rows, header declares {expected}")
        all_rows.extend(rows)
        season_rows = pd.DataFrame(rows)
        base = f"https://raw.githubusercontent.com/openfootball/champions-league/master/{season_rows.season.iloc[0]}/cl.txt"
        manifest.append({
            "season": season_rows.season.iloc[0],
            "source_url": base,
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
            "header_match_count": expected,
            "parsed_match_count": len(rows),
            "parsed_team_count": pd.unique(pd.concat([season_rows.home_team, season_rows.away_team])).size,
            "date_min": season_rows.date.min(),
            "date_max": season_rows.date.max(),
        })
    frame = pd.DataFrame(all_rows)
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["date", "kickoff_time", "season"], na_position="last").reset_index(drop=True)
    frame.to_csv(OUT_DIR / "ucl_matches.csv", index=False)
    (ROOT / "data" / "metadata").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(manifest).to_csv(ROOT / "data" / "metadata" / "ucl_source_manifest.csv", index=False)
    print(f"Parsed {len(frame)} matches from {len(files)} files")
    print(frame.groupby(["season", "competition_phase"], dropna=False).size().to_string())
    print("90-minute outcomes parsed:", int(frame["outcome_90m"].notna().sum()))
    print("Unresolved 90-minute outcomes:", int(frame["outcome_90m"].isna().sum()))
    print("Duplicate match keys:", int(frame.duplicated(["date", "home_team", "away_team"]).sum()))


if __name__ == "__main__":
    main()
