from pathlib import Path

import pandas as pd

from cli_args import parse_conference_season


def extract_team_per_game(html_path: Path, season_end_year: int) -> pd.DataFrame | None:
    """
    Given a Sports-Reference team HTML file, return the per-game player stats table
    as a DataFrame, or None if not found.
    """
    print(f"Parsing {html_path.name} ...")

    try:
        # read_html will pull all tables on the page into a list of DataFrames
        tables = pd.read_html(html_path, flavor="bs4")
    except ValueError:
        print(f"  No tables found in {html_path.name}")
        return None

    candidate = None
    for df in tables:
        cols = [str(c) for c in df.columns]
        # Heuristic: per-game table has 'Player' and 'G' columns
        if "Player" in cols and "G" in cols:
            candidate = df
            break

    if candidate is None:
        print(f"  No per-game player table found in {html_path.name}")
        return None

    df = candidate.copy()

    # Normalize column names to strings
    df.columns = [str(c) for c in df.columns]

    # Drop rows that are clearly totals or non-players
    if "Player" in df.columns:
        df = df[df["Player"].notna()]
        bad_labels = {"Team", "Team Totals", "Opponents", "Opponent"}
        df = df[~df["Player"].isin(bad_labels)]

    # Add team + season metadata
    team_slug = html_path.stem.replace(f"_{season_end_year}", "")
    df.insert(0, "team_slug", team_slug)
    df.insert(1, "season_end_year", season_end_year)

    return df


def main() -> None:
    # Use shared CLI: returns (ConferenceConfig, season_end_year)
    conf, season_end_year = parse_conference_season()

    project_root = Path(__file__).resolve().parents[1]

    # Match the scraper's directory pattern: e.g. "2024-2025"
    season_label = f"{season_end_year - 1}-{season_end_year}"

    raw_dir = (
        project_root
        / "ncaa-analytics"
        / "data_raw"
        / conf.data_subdir
        / season_label
    )

    out_dir = (
        project_root
        / "ncaa-analytics"
        / "data_intermediate"
        / conf.data_subdir
        / season_label
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Conference: {conf.name} ({conf.key})")
    print(f"Season end year: {season_end_year}")
    print(f"Reading HTML from: {raw_dir}")
    print(f"Writing CSVs to:   {out_dir}\n")

    all_dfs: list[pd.DataFrame] = []

    for html_path in sorted(raw_dir.glob("*.html")):
        df = extract_team_per_game(html_path, season_end_year)
        if df is None:
            continue

        out_csv = out_dir / f"{html_path.stem}_per_game.csv"
        df.to_csv(out_csv, index=False)
        all_dfs.append(df)
        print(f"  -> wrote {out_csv.name} ({len(df)} rows)")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_csv = out_dir / \
            f"{conf.key}_{season_end_year}_per_game_all_teams.csv"
        combined.to_csv(combined_csv, index=False)
        print(
            f"\nWrote combined file: {combined_csv.name} ({len(combined)} rows)"
        )
    else:
        print("No per-game tables parsed for any team.")


if __name__ == "__main__":
    main()
