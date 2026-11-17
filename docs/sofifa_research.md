# Historical FIFA / SoFIFA player data: source audit

**Status:** source discovery only. No player ratings have been added to the match table or model. Ratings remain an optional feature candidate pending a time-safe join and a fair ablation.

## Findings

**Disposition in the evaluated project:** FIFA/SoFIFA player attributes were researched but were not joined to UCL matches, added to a feature set, or evaluated as Model D. The FIFA 15–23 annual file has one snapshot per edition and cannot guarantee contemporaneous squad coverage across later evaluation seasons. The 5.6 GB all-updates archive was not downloaded or audited. Other later snapshots have uncertain capture provenance, incomplete time coverage, and unverified club joins. Snapshot club does not prove UCL registration or match participation; complete historical, pre-kickoff lineups are not available in the current match data. These gaps prevent a fair common-row, leakage-safe Model D comparison.

| Edition / source | Snapshot coverage found | Useful fields | Limits for this project |
|---|---|---|---|
| FIFA 14 community CSV | One FIFA 14 Ultimate Team card dump (14,735 CSV lines); its `LOADDATE` is 2018-09-19, not the date of the rating snapshot | Card rating, six broad card attributes, club and position | No player ID or birth date; repeated special-card versions; not a clean career-mode player rating snapshot. Do not use as the primary source. |
| FIFA 15–23 all-updates file (male_players.csv) | Dataset card says all updates from 2015-09-10 through 2023-01-13; Hugging Face lists the file at 5,637,105,640 bytes (about 5.6 GB) | player_id, fifa_version, fifa_update, fifa_update_date, club/team, positions, overall and detailed attributes | Strongest update-level candidate, but the full file was not downloaded or audited because of its size. The HF dataset viewer currently reports a schema-cast failure across mixed legacy/new files. Claims about per-update coverage, IDs, and joins remain provisional until this file is obtained and checked. |
| FIFA 15–23 “legacy” male-player CSV (audited) | One dated snapshot per edition: FIFA 15–23, dated 2014-09-18 through 2022-09-26 | player_id, update date, club/team, positions, overall and detailed attributes | Downloaded outside the project for source audit only. 161,583 rows, 49,699 unique non-null IDs, 0 missing IDs, and no duplicate player/edition/update rows. It has only one update per edition and is not the all-updates file. |
| EA FC 24 SoFIFA mirror | Downloaded and inspected `all_fifa_players.csv`: 37,158 rows × 77 columns; 18,579 distinct non-null `Player ID`s. Source filenames encode 2024-11-12; the file combines an all-player file with league files, so repeated IDs are not separate players. | Player ID, club/league, position, overall and detailed attributes | No FIFA version/update date column; a source filename timestamp is weaker provenance than an explicit release timestamp. This snapshot is after the first 2024/25 UCL matchdays, so it cannot be used for those earlier matches. The page declares GPL-3.0, but the underlying scraped-data rights should be checked before redistribution. |
| EA FC 25 SoFIFA download | A public dataset labeled 2025-06-03 was identified | Current roster and rating attributes | One snapshot, not an in-season update history. It postdates every 2024/25 UCL match; if its timestamp is confirmed, it is chronologically before 2025/26 kickoffs but the ratings and clubs may be stale by then. |
| EA FC 26 player database | One downloadable snapshot updated 2026-04-02 was identified | Player IDs, club, position and rating categories | Not a historical update series. It is usable only for matches after the snapshot date; it cannot represent earlier 2025/26 fixtures. |

The broadest candidate is the FIFA 15–23 all-updates file, but the actual bulk file is very large and has not been audited. The smaller legacy CSV is a practical annual-snapshot alternative, not evidence that every update is available in that file. Its rows cover all nine editions FIFA 15–23; FIFA 14 does not offer a clean ID-linked continuation in the community dump reviewed. SoFIFA version-history tooling documents release/update discovery but is a live source; no live site scraping was performed.

## Time alignment to the parsed UCL seasons

The full all-updates file is reported to span 2015-09-10 through 2023-01-13, but those dates have not been checked row-by-row because the 5.6 GB file was not downloaded. The audited legacy file instead has nine edition snapshots (2014-09-18 through 2022-09-26). For that file, the latest snapshot strictly before each match was no more than 365 days old for all 125 matches in each season from 2015/16 through 2018/19, 103/119 in 2019/20, and all matches in 2020/21 through 2022/23. Only 16/125 matches in 2023/24 have a legacy snapshot no more than 365 days old; none in 2024/25 or 2025/26 do. All matches have some strictly earlier legacy snapshot if arbitrarily stale ratings are accepted, but that is not meaningful contemporaneous coverage. Day-level dates require strict earlier-than-match-date alignment unless an exact publication time proves availability before kickoff.

| UCL dates | Candidate FIFA/SoFIFA data | Time-safe implication |
|---|---|---|
| 2015/16–2021/22 | Audited legacy annual snapshots; full all-updates file reported for these editions but unaudited | Legacy latest-snapshot age is ≤365 days for all matches in 2015/16–2018/19, 103/119 in 2019/20, and all in 2020/21–2021/22. Actual update-level availability requires auditing the 5.6 GB file. |
| 2022/23 | Legacy FIFA 23 snapshot 2022-09-26; full all-updates file reported through 2023-01-13 | Early September group matches precede the FIFA 23 snapshot and must use prior FIFA 22 (2021-09-23); the latest eligible legacy snapshot is ≤365 days old for all 125 matches. Update-level availability remains unverified. |
| 2023/24 | Legacy FIFA 23 snapshot 2022-09-26; all-updates file reported through 2023-01-13; FC24 mirror dated 2024-11-12 | The legacy snapshot is chronologically prior but only ≤365 days old for 16/125 matches. The reported all-updates cutoff precedes the whole season; FC24 is after the whole season and cannot be backfilled. |
| 2024/25 | Legacy FIFA 23 / all-updates archive ends in 2022/23; FC24 mirror date 2024-11-12; FC25 download date 2025-06-03 | FC24’s file date is before 117/189 match dates, if it is the actual capture date; FC25 postdates the season and is invalid for it. The legacy FIFA 23 ratings are stale by over 700 days throughout. |
| 2025/26 | FC25 snapshot 2025-06-03; FC26 database updated 2026-04-02 | FC25’s dated snapshot precedes all 189 match dates and is a possible squad proxy if capture date/schema are confirmed. FC26’s snapshot precedes only 13 match dates. The older FIFA 15–23 data is highly stale. |

The legacy-snapshot age counts above were calculated against parsed UCL match dates using a strict snapshot-date-before-match-date rule. They measure only calendar availability, not usable player coverage, correct club mapping, a complete squad, or competition registration. The separate FC24 match-date count likewise reflects only the filename date, not a confirmed capture timestamp.

A practical first Model D test can use the audited annual legacy snapshots for earlier seasons, with snapshot age included and threshold sensitivity reported. The ID audit is encouraging but not conclusive: across 49,699 IDs, 828 IDs (1.67%) have more than one long-name spelling/value and 1,428 (2.87%) have more than one date-of-birth value; these may reflect corrections, inconsistent records, or identity issues. Three exact long-name/date-of-birth identities map to multiple IDs. Use player_id as the candidate key, corroborate with name and birth date, and inspect exceptions. The 2025/26 FC25 single-snapshot test remains a possible separate ablation, scored on identical 2025/26 rows for Models A–C. Do not claim one consistent full-coverage 2023/24–2025/26 player-feature test. Club-name mappings and actual roster/lineup coverage remain unverified.

## IDs and club membership

SoFIFA IDs are intended to identify a player across editions. In the audited annual legacy CSV, player_id is non-null on all 161,583 rows, and each ID appears in a median of 2 editions (maximum 9). Most repeated IDs retain the same name and birth date, but the inconsistencies quantified above mean IDs should be corroborated against birth date and normalized name before joins. The full all-updates CSV remains unaudited. Do not join on player name alone: names can vary, collide, or change, and legacy/icon records can be reintroduced or have gaps.

Club/team on a player row means the club attached to that particular game-data snapshot. It is not a complete transfer history, a UEFA registration list, or proof the player was eligible for that UCL match. A snapshot can only stand in for a historical roster when its verified capture/update time predates kickoff; with day-only dates, require a strictly earlier date. Even then it may not match competition registration.

## Lineups and squad-vs-starting-XI features

The FIFA/SoFIFA player archives describe player databases and club assignment at update time; they do not give the actual starting XI for each UCL match. OpenFootball's UCL files provide schedules/results, not historical lineups. StatsBomb Open Data has match lineups for selected competitions/seasons, including selected Champions League history, but its UCL coverage is not a full recent-season lineup panel. Transfermarkt's downloadable player-scores archive includes `game_lineups` and appearance tables and is a possible separate candidate; coverage for the exact UCL seasons and reuse terms need checking before use.

Keep these feature types separate:

1. **Snapshot squad proxy:** summarize players assigned to the club in a dated FIFA/SoFIFA snapshot. This is not a confirmed UCL roster or match XI.
2. **Actual starting XI:** join a match-specific lineup and rate those starters. This more closely represents who played, but only use it for a pre-kickoff prediction if the lineup was publicly available before the assumed prediction time. A lineup recorded after the match without an announcement timestamp does not by itself prove availability before kickoff.

## Candidate aggregates

For any experiment, start with explainable, pre-match club summaries from the latest snapshot with a verified publication/update time before kickoff (or strictly earlier match date when only day-level dates exist): mean/median overall rating; mean attacking, passing/dribbling, defensive, and goalkeeper attributes; position-group mean overall for GK / defence / midfield / attack; squad size and counts with missing attributes; then home-minus-away differences. Use position/attribute groups, not end-of-season team standings or players observed only because they appeared in the target match. Keep snapshot-squad and actual-lineup aggregates in separate model variants.

For each match define the snapshot as the maximum snapshot date strictly earlier than the match date when only a calendar date is available, or the latest verified publication timestamp before kickoff. An absent eligible snapshot must stay missing; never fill it from a later edition. Report feature coverage by match, season, team, and stage. Compare Models A–C and Model D on identical chronological test rows and probabilities, using log loss and multiclass Brier score as primary incremental-value measures. The all-updates file remains unaudited; the final 2023/24–2025/26 test block has no verified contemporaneous FIFA 15–23 update coverage.

## Recommended direction

Keep player ratings as an optional research ablation, but do not add them to the production model based on the currently audited annual snapshots alone. First decide whether the 5.6 GB all-updates file can be obtained and audited in a controlled way; otherwise use the legacy snapshots only for a clearly labeled stale-squad sensitivity experiment. Audit later one-off snapshots separately. If exact lineups are missing, call aggregates squad proxies and never lineup strength.

## Sources

- [SoFIFA version/update reader documentation](https://soccerdata.readthedocs.io/en/latest/reference/sofifa.html) (documents selectable FIFA versions, release/update discovery, player and rating readers).
- [FIFA 15–23 complete player dataset card](https://huggingface.co/datasets/jsulz/FIFA23) and [Kaggle dataset](https://www.kaggle.com/datasets/stefanoleone992/fifa-23-complete-player-dataset) (coverage, update dates, field history, source attribution to SoFIFA).
- [FIFA 14 community CSV](https://raw.githubusercontent.com/kafagy/fifa-FUT-Data/master/FIFA14.csv) (schema checked: no player ID; FUT card fields and load date).
- [EA FC 24 mirror and file listing](https://huggingface.co/datasets/jmacd867/SoFifa-Dataset-2024/tree/main) (downloaded file inspected for schema, row count, duplicate IDs and source-file timestamps).
- [EA FC 25 June 2025 dataset](https://www.kaggle.com/datasets/aniss7/fifa-player-data-from-sofifa-2025-06-03).
- [EA FC 26 player database](https://www.kaggle.com/datasets/flynn28/eafc26-player-database) (dataset page describes the 2026-04-02 update).
- [Football.TXT format specification](https://openfootball.github.io/spec/) and [OpenFootball Champions League repository](https://github.com/openfootball/champions-league) (match results format and source data).
- [StatsBomb Open Data](https://github.com/hudl/open-data) (lineups are available for selected match/season files).
- [Transfermarkt player-scores dataset project](https://github.com/dcaribou/transfermarkt-datasets) (documents games, appearances, game lineups, clubs, players and other bulk tables).

## Acquisition and reproducibility note

The FC24 mirror CSV and FIFA 15–23 legacy male-player CSV were downloaded temporarily for schema audits; neither was copied into project data directories. The 5.6 GB all-updates male-player CSV was not downloaded.
