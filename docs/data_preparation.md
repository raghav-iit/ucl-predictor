# Match-data parsing and validation

The original Football.TXT files under `data/raw/` are preserved unchanged. Historical OpenFootball season files for 2015/16–2023/24 were added alongside them. Run the parser from the repository with:

```bash
.venv/bin/python src/parse_football_txt.py
```

It writes `data/processed/ucl_matches.csv` and `data/metadata/ucl_source_manifest.csv`. The match table keeps season, date, kickoff time, raw stage heading, normalized competition phase, format era, home/away team, 90-minute goals and outcome, any listed after-extra-time score, penalty shootout score, and source file/line. Raw files are not modified.

The parser follows the [Football.TXT score specification](https://openfootball.github.io/spec/). In ordinary scorelines, the result is the regulation score. In AET notation, it uses the documented regulation-time score component where provided. A 0–0 after-extra-time score implies a 0–0 regulation score when the source omits a separate regulation component. Penalty shootout goals are stored separately and never treated as match goals. If a source record does not identify regulation time unambiguously, the parser leaves the target missing rather than guessing. Matches sharing a date inherit the most recently stated kickoff time within a same-time group, as repeated times are omitted in Football.TXT.

Dates without a year are assigned using the date range declared in each raw file header. Parsed rows outside that header interval cause a parsing error. This matters for 2019/20, when the tournament resumed in August 2020 after the pandemic pause.

## Parsed season coverage

| Season | Matches | League/group phase | Knockout playoffs | Other knockouts | Teams | Date range |
|---|---:|---:|---:|---:|---:|---|
| 2015–16 | 125 | 96 | 0 | 29 | 32 | 2015-09-15 to 2016-05-28 |
| 2016–17 | 125 | 96 | 0 | 29 | 32 | 2016-09-13 to 2017-06-03 |
| 2017–18 | 125 | 96 | 0 | 29 | 32 | 2017-09-12 to 2018-05-26 |
| 2018–19 | 125 | 96 | 0 | 29 | 32 | 2018-09-18 to 2019-06-01 |
| 2019–20 | 119 | 96 | 0 | 23 | 32 | 2019-09-17 to 2020-08-23 |
| 2020–21 | 125 | 96 | 0 | 29 | 32 | 2020-10-20 to 2021-05-29 |
| 2021–22 | 125 | 96 | 0 | 29 | 32 | 2021-09-14 to 2022-05-28 |
| 2022–23 | 125 | 96 | 0 | 29 | 32 | 2022-09-06 to 2023-06-10 |
| 2023–24 | 125 | 96 | 0 | 29 | 32 | 2023-09-19 to 2024-06-01 |
| 2024–25 | 189 | 144 | 16 | 29 | 36 | 2024-09-17 to 2025-05-31 |
| 2025–26 | 189 | 144 | 16 | 29 | 36 | 2025-09-16 to 2026-05-30 |

The parsed total is **1,497 matches**. Every source file's parsed count matches its `# Matches` header; the output has no duplicate `(date, home team, away team)` keys and no missing 90-minute outcomes. Source URL, SHA-256, byte size, header count, parsed count, team count and date coverage are recorded in the manifest. Header agreement validates internal consistency with OpenFootball's declared counts, not completeness against an independent official match archive.

## Label and format notes

The finalized primary target is `outcome_90m`: `H`, `D`, or `A` after 90 minutes. The table also retains the after-extra-time result and shootout score so a later tournament simulation can model advancement separately. The current source set begins at the main group stage; qualifying-round coverage is not included.

`competition_phase` separates old group stages/new league phases, the 2024/25-onward knockout playoffs, and other knockout rounds. `format_era` distinguishes the 32-team group-stage seasons through 2023/24 from the 36-team league-phase format introduced in 2024/25. Keep the old group stage and new league phase separate in the primary phase analysis.
