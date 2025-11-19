import argparse
from conferences import CONFERENCES, ConferenceConfig


def parse_conference_season():
    """
    Parse CLI args and return (ConferenceConfig, season_end_year).
    Example:
      python scrape_conference_season.py --conference sun-belt --season 2025
    """
    parser = argparse.ArgumentParser(
        description="Scrape Sports-Reference team pages for a given conference & season."
    )

    parser.add_argument(
        "--conference",
        required=True,
        choices=sorted(CONFERENCES.keys()),
        help="Conference key (e.g. 'sun-belt').",
    )
    parser.add_argument(
        "--season",
        required=True,
        type=int,
        help="Season end year, e.g. 2025 for the 2024-25 season.",
    )

    args = parser.parse_args()
    conf: ConferenceConfig = CONFERENCES[args.conference]
    season_end_year: int = args.season

    return conf, season_end_year
