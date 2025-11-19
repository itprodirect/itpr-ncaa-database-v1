from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ConferenceConfig:
    key: str                    # e.g. "sun-belt"
    name: str                   # e.g. "Sun Belt"
    sportsref_slug: str         # e.g. "sun-belt"
    sportsref_team_slugs: List[str]  # sports-reference school slugs
    data_subdir: str            # subdir under ncaa-analytics/data_raw/


CONFERENCES: dict[str, ConferenceConfig] = {
    "sun-belt": ConferenceConfig(
        key="sun-belt",
        name="Sun Belt Conference",
        sportsref_slug="sun-belt",
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

    "sec": ConferenceConfig(
        key="sec",
        name="Southeastern Conference",
        sportsref_slug="sec",
        sportsref_team_slugs=[
            "alabama",
            "arkansas",
            "auburn",
            "florida",
            "georgia",
            "kentucky",
            "lsu",
            "mississippi",
            "mississippi-state",
            "missouri",
            "south-carolina",
            "tennessee",
            "texas-am",
            "vanderbilt",
        ],
        data_subdir="sec",
    ),
}
