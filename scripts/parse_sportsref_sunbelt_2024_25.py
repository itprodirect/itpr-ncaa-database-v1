from pathlib import Path

import pandas as pd

# -------------------------
# Paths
# -------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = (
    PROJECT_ROOT
    / "ncaa-analytics"
    / "data_raw"
    / "sun_belt"
    / "2024-25"
)

OUT_DIR = (
    PROJECT_ROOT
    / "ncaa-analytics"
    / "data_intermediate"
    / "sun_belt"
    / "2024-25"
)

SPORTSREF_YEAR = 2025  # 2024-25 season


# -------------------------
# Core parsing logic
# -------------------------

def extract_team_per_game(html_path: Path) -> pd.DataFrame | None:
    """
    Given a Sports-Reference team HTML file, return the per-game player stats table
    as a DataFrame, or None if not found.
    """
    print(f"Parsing {html_path.name} ...")

    # read_html will pull all tables on the page into a list of DataFrames
    try:
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
    team_slug = html_path.stem.replace(f"_{SPORTSREF_YEAR}", "")
    df.insert(0, "team_slug", team_slug)
    df.insert(1, "season", SPORTSREF_YEAR)

    return df


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_dfs = []

    for html_path in sorted(RAW_DIR.glob("*.html")):
        df = extract_team_per_game(html_path)
        if df is None:
            continue

        out_csv = OUT_DIR / f"{html_path.stem}_per_game.csv"
        df.to_csv(out_csv, index=False)
        all_dfs.append(df)
        print(f"  -> wrote {out_csv.name} ({len(df)} rows)")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_csv = OUT_DIR / "sun_belt_2024_25_per_game_all_teams.csv"
        combined.to_csv(combined_csv, index=False)
        print(
            f"\nWrote combined file: {combined_csv.name} ({len(combined)} rows)")
    else:
        print("No per-game tables parsed for any team.")


if __name__ == "__main__":
    main()
