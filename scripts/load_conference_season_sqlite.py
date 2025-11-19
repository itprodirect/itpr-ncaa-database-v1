import sqlite3
from pathlib import Path

import pandas as pd

from cli_args import parse_conference_season

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "ncaa-analytics" / "db" / "ncaa_dev.db"


def upsert_conference(conn, conf):
    conn.execute(
        "INSERT OR IGNORE INTO conferences (conference_key, name) VALUES (?, ?)",
        (conf.key, conf.name),
    )


def get_or_create_player_ids(conn, names: list[str]) -> dict[str, int]:
    """
    Return mapping {player_name -> player_id}.
    Very simple: uniqueness by name only for now.
    """
    cur = conn.cursor()
    ids: dict[str, int] = {}

    for name in names:
        if name in ids:
            continue
        cur.execute(
            "SELECT player_id FROM players WHERE player_name = ?", (name,))
        row = cur.fetchone()
        if row:
            ids[name] = row[0]
        else:
            cur.execute(
                "INSERT INTO players (player_name) VALUES (?)", (name,))
            ids[name] = cur.lastrowid

    return ids


def load_stats_and_rosters(conf, season_end_year: int):
    season_label = f"{season_end_year - 1}-{season_end_year}"

    interm_dir = (
        PROJECT_ROOT
        / "ncaa-analytics"
        / "data_intermediate"
        / conf.data_subdir
        / season_label
    )

    stats_csv = interm_dir / \
        f"{conf.key}_{season_end_year}_per_game_all_teams.csv"
    roster_csv = interm_dir / \
        f"{conf.key}_{season_end_year}_roster_all_teams.csv"

    if not stats_csv.exists():
        raise FileNotFoundError(f"Missing stats CSV: {stats_csv}")
    if not roster_csv.exists():
        raise FileNotFoundError(f"Missing roster CSV: {roster_csv}")

    stats_df = pd.read_csv(stats_csv)
    roster_df = pd.read_csv(roster_csv)

    # Normalise column names
    stats_df.columns = [c.lower() for c in stats_df.columns]
    roster_df.columns = [c.lower() for c in roster_df.columns]

    # Ensure required metadata exists
    # stats parser added: team_slug, season_end_year
    if "team_slug" not in stats_df.columns or "season_end_year" not in stats_df.columns:
        raise ValueError("Stats CSV missing team_slug or season_end_year.")

    if "team_slug" not in roster_df.columns or "season_end_year" not in roster_df.columns:
        raise ValueError("Roster CSV missing team_slug or season_end_year.")

    # Align on player name key
    # stats: "player", roster: "player"
    stats_df["player_name"] = stats_df["player"].astype(str).str.strip()
    roster_df["player_name"] = roster_df["player"].astype(str).str.strip()

    return stats_df, roster_df


def main():
    conf, season_end_year = parse_conference_season()
    stats_df, roster_df = load_stats_and_rosters(conf, season_end_year)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    with conn:
        upsert_conference(conn, conf)

        # teams
        team_slugs = sorted(stats_df["team_slug"].unique())
        for slug in team_slugs:
            conn.execute(
                "INSERT OR IGNORE INTO teams (team_slug, conference_key, school_name) VALUES (?, ?, NULL)",
                (slug, conf.key),
            )

        # players
        all_names = sorted(set(stats_df["player_name"]) | set(
            roster_df["player_name"]))
        name_to_id = get_or_create_player_ids(conn, all_names)

        # player_season_stats
        stats_rows = []
        for _, row in stats_df.iterrows():
            pid = name_to_id[row["player_name"]]
            stats_rows.append(
                (
                    pid,
                    row["team_slug"],
                    conf.key,
                    int(row["season_end_year"]),
                    row.get("g"),
                    row.get("mp"),
                    row.get("pts"),
                    row.get("trb") or row.get("reb"),
                    row.get("ast"),
                )
            )

        conn.executemany(
            """
            INSERT OR REPLACE INTO player_season_stats
            (player_id, team_slug, conference_key, season_end_year,
             g, mp, pts, reb, ast)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            stats_rows,
        )

        # player_roster_attrs
        roster_rows = []
        for _, row in roster_df.iterrows():
            name = row["player_name"]
            pid = name_to_id.get(name)
            if pid is None:
                continue
            roster_rows.append(
                (
                    pid,
                    row["team_slug"],
                    conf.key,
                    int(row["season_end_year"]),
                    row.get("class_year"),
                    row.get("pos"),
                    row.get("height_cm"),
                    row.get("weight_kg"),
                )
            )

        conn.executemany(
            """
            INSERT OR REPLACE INTO player_roster_attrs
            (player_id, team_slug, conference_key, season_end_year,
             class_year, pos, height_cm, weight_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            roster_rows,
        )

    conn.close()
    print(
        f"Loaded {len(stats_rows)} season stat rows and {len(roster_rows)} roster rows into {DB_PATH}")


if __name__ == "__main__":
    main()
