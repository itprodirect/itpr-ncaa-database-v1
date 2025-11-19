import time
from pathlib import Path

import requests

from cli_args import parse_conference_season


BASE_URL = "https://www.sports-reference.com/cbb/schools"
HEADERS = {
    # Use a browser-y UA string so we don't get weird stripped-down pages
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36 itpr-ncaa-db/0.1"
    )
}


def fetch_team_html(slug: str, season_end_year: int) -> tuple[str, str]:
    """
    Fetch the HTML for a single team season page.

    Example URL:
      https://www.sports-reference.com/cbb/schools/appalachian-state/men/2025.html
    """
    url = f"{BASE_URL}/{slug}/men/{season_end_year}.html"
    resp = requests.get(url, headers=HEADERS, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} for {url}")

    return resp.text, url


def main() -> None:
    conf, season_end_year = parse_conference_season()

    project_root = Path(__file__).resolve().parents[1]

    # E.g. ncaa-analytics/data_raw/sun_belt/2024-2025
    season_dir_name = f"{season_end_year - 1}-{season_end_year}"
    raw_dir = (
        project_root
        / "ncaa-analytics"
        / "data_raw"
        / conf.data_subdir
        / season_dir_name
    )
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Conference: {conf.name} ({conf.key})")
    print(f"Season end year: {season_end_year}")
    print(f"Saving HTML files under: {raw_dir}\n")

    for slug in conf.sportsref_team_slugs:
        print(f"Fetching {slug} ... ", end="", flush=True)
        try:
            html, url = fetch_team_html(slug, season_end_year)
        except Exception as exc:
            print(f"ERROR -> {exc}")
            continue

        out_path = raw_dir / f"{slug}_{season_end_year}.html"
        out_path.write_text(html, encoding="utf-8")
        rel_path = out_path.relative_to(project_root)
        print(f"ok -> {url} -> {rel_path}")

        # Be polite to the site: tiny delay between requests
        time.sleep(1.0)


if __name__ == "__main__":
    main()
