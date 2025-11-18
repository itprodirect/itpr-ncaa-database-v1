from pathlib import Path
import sqlite3

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "ncaa-analytics"
    / "data_intermediate"
    / "sun_belt"
    / "2024-25"
    / "sun_belt_2024_25_per_game_all_teams.csv"
)

DB_PATH = PROJECT_ROOT / "ncaa-analytics" / "db" / "ncaa_dev.db"
TABLE_NAME = "player_per_game_sun_belt_2024_25"


def load_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)

    # Normalize column names for SQL (no %, spaces, etc.)
    rename_map = {
        "Rk": "rk",
        "Player": "player",
        "Pos": "pos",
        "G": "g",
        "GS": "gs",
        "MP": "mp",
        "FG": "fg",
        "FGA": "fga",
        "FG%": "fg_pct",
        "3P": "fg3",
        "3PA": "fg3a",
        "3P%": "fg3_pct",
        "2P": "fg2",
        "2PA": "fg2a",
        "2P%": "fg2_pct",
        "eFG%": "efg_pct",
        "FT": "ft",
        "FTA": "fta",
        "FT%": "ft_pct",
        "ORB": "orb",
        "DRB": "drb",
        "TRB": "trb",
        "AST": "ast",
        "STL": "stl",
        "BLK": "blk",
        "TOV": "tov",
        "PF": "pf",
        "PTS": "pts",
        "Awards": "awards",
        "team_slug": "team_slug",
        "season": "season",
    }

    df = df.rename(columns=rename_map)

    # Optional: enforce some basic types
    df["season"] = df["season"].astype(int)
    df["team_slug"] = df["team_slug"].astype(str)
    df["player"] = df["player"].astype(str)

    return df


def write_to_sqlite(df: pd.DataFrame) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Replace table each time for now
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

        # Simple index to speed up lookups
        with conn:
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_team_season "
                f"ON {TABLE_NAME} (team_slug, season)"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_player "
                f"ON {TABLE_NAME} (player)"
            )

    finally:
        conn.close()


def main():
    print(f"Loading CSV from: {CSV_PATH}")
    df = load_csv()
    print(f"Loaded {len(df)} rows")

    print(f"Writing to SQLite DB: {DB_PATH} (table={TABLE_NAME})")
    write_to_sqlite(df)
    print("Done.")


if __name__ == "__main__":
    main()
