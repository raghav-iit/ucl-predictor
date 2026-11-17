from __future__ import annotations

import re
import unicodedata

# Curated mappings for club-name variants seen in the OpenFootball files.
ALIASES = {
    "bayer 04 leverkusen": "bayer leverkusen",
    "atalanta bc": "atalanta",
    "gnk dinamo zagreb": "dinamo zagreb",
    "internazionale milano": "inter",
    "inter": "inter",
    "lazio roma": "lazio",
    "ss lazio": "lazio",
    "olympiakos piraeus": "olympiakos",
    "olympiakos sfp": "olympiakos",
    "rb salzburg": "salzburg",
    "red bull salzburg": "salzburg",
    "fc red bull salzburg": "salzburg",
    "psv eindhoven": "psv",
    "sl benfica": "benfica",
    "sport lisboa benfica": "benfica",
    "qarabag agdam": "qarabag",
    "qarabag fk": "qarabag",
    "feyenoord rotterdam": "feyenoord",
    "sporting cp": "sporting portugal",
    "sporting clube de portugal": "sporting portugal",
    "bor monchengladbach": "borussia monchengladbach",
}


def team_key(source_name: str) -> str:
    """Normalize source club labels and apply reviewed cross-season aliases."""
    name = re.sub(r"\s+\([A-Z]{3}\)$", "", str(source_name)).strip()
    name = "".join(
        char for char in unicodedata.normalize("NFKD", name)
        if not unicodedata.combining(char)
    ).lower()
    name = name.replace("&", " and ").replace("-", " ")
    tokens = re.findall(r"[a-z0-9]+", name)
    structural = {
        "fc", "cf", "sc", "afc", "ac", "as", "ss", "ssc", "fk", "sk",
        "pae", "bsc", "ff", "sv", "vfl", "club", "de", "del", "da",
        "do", "futbol", "football", "clube", "e",
    }
    tokens = [token for token in tokens if token not in structural and not token.isdigit()]
    normalized = " ".join(tokens)
    return ALIASES.get(normalized, normalized)

