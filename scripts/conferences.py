from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ConferenceConfig:
    key: str                    # e.g. "sun-belt"
    name: str                   # e.g. "Sun Belt"
    sportsref_slug: str         # e.g. "sun-belt" (for future use if needed)
    sportsref_team_slugs: List[str]  # sports-reference school slugs
    data_subdir: str            # subdir under ncaa-analytics/data_raw/


CONFERENCES: Dict[str, ConferenceConfig] = {
    "sun-belt": ConferenceConfig(
        key="sun-belt",
        name="Sun Belt Conference",
        sportsref_slug="sun-belt",
        # These are the official Sports-Reference school slugs for 2024–25 Sun Belt teams
        sportsref_team_slugs=[
            "appalachian-state",
            "arkansas-state",
            "coastal-carolina",
            "georgia-southern",
            "georgia-state",
            "james-madison",
            "louisiana-lafayette",
            "louisiana-monroe",
            "marshall",
            "old-dominion",
            "south-alabama",
            "southern-mississippi",
            "texas-state",
            "troy",
        ],
        data_subdir="sun_belt",
    ),

    # 🔜 Later we’ll add SEC, ACC, etc. here:
    # "sec": ConferenceConfig(...),
    # "acc": ConferenceConfig(...),
}
