import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve(
).parents[1] / "ncaa-analytics" / "db" / "ncaa_dev.db"

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS conferences (
    conference_key TEXT PRIMARY KEY,
    name          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    team_slug      TEXT PRIMARY KEY,
    conference_key TEXT NOT NULL,
    school_name    TEXT,
    FOREIGN KEY (conference_key) REFERENCES conferences(conference_key)
);

CREATE TABLE IF NOT EXISTS players (
    player_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name    TEXT NOT NULL,
    -- later: canonical_id, birthdate, etc.
    UNIQUE(player_name)
);

CREATE TABLE IF NOT EXISTS player_season_stats (
    player_id        INTEGER NOT NULL,
    team_slug        TEXT NOT NULL,
    conference_key   TEXT NOT NULL,
    season_end_year  INTEGER NOT NULL,
    -- raw stats as TEXT/REAL (add what you need):
    g                REAL,
    mp               REAL,
    pts              REAL,
    reb              REAL,
    ast              REAL,
    -- etc...
    PRIMARY KEY(player_id, team_slug, season_end_year),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_slug) REFERENCES teams(team_slug),
    FOREIGN KEY (conference_key) REFERENCES conferences(conference_key)
);

CREATE TABLE IF NOT EXISTS player_roster_attrs (
    player_id        INTEGER NOT NULL,
    team_slug        TEXT NOT NULL,
    conference_key   TEXT NOT NULL,
    season_end_year  INTEGER NOT NULL,
    class_year       TEXT,
    pos              TEXT,
    height_cm        REAL,
    weight_kg        REAL,
    PRIMARY KEY(player_id, team_slug, season_end_year),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_slug) REFERENCES teams(team_slug),
    FOREIGN KEY (conference_key) REFERENCES conferences(conference_key)
);
"""


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.executescript(DDL)
    conn.close()
    print(f"Initialized schema at {DB_PATH}")


if __name__ == "__main__":
    main()
