from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# -----------------------------
# Config / DB helpers
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "ncaa-analytics" / "db" / "ncaa_dev.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_conferences():
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT conference_key, name FROM conferences ORDER BY conference_key",
            conn,
        )
    return df


def get_seasons(conference_key: str):
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT DISTINCT season_end_year
            FROM player_season_stats
            WHERE conference_key = ?
            ORDER BY season_end_year DESC
            """,
            conn,
            params=(conference_key,),
        )
    return df["season_end_year"].tolist()


def get_teams(conference_key: str, season_end_year: int):
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT DISTINCT team_slug
            FROM player_season_stats
            WHERE conference_key = ? AND season_end_year = ?
            ORDER BY team_slug
            """,
            conn,
            params=(conference_key, season_end_year),
        )
    return df["team_slug"].tolist()


def get_player_profiles(conference_key, season_end_year, team_slug, name_filter):
    query = """
        SELECT
            p.player_name,
            s.team_slug,
            s.conference_key,
            s.season_end_year,
            s.g,
            s.mp,
            s.pts,
            s.reb,
            s.ast,
            r.class_year,
            r.pos,
            r.height_cm,
            r.weight_kg
        FROM player_season_stats s
        JOIN players p
            ON p.player_id = s.player_id
        LEFT JOIN player_roster_attrs r
            ON r.player_id = s.player_id
           AND r.team_slug = s.team_slug
           AND r.season_end_year = s.season_end_year
        WHERE s.conference_key = ?
          AND s.season_end_year = ?
    """

    params = [conference_key, season_end_year]

    if team_slug and team_slug != "__ALL__":
        query += " AND s.team_slug = ?"
        params.append(team_slug)

    if name_filter:
        query += " AND p.player_name LIKE ?"
        params.append(f"%{name_filter}%")

    query += " ORDER BY s.team_slug, p.player_name"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    return df


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="NCAA Database V1", layout="wide")

st.title("🏀 NCAA Player Database V1")
st.caption("Backed by your SQLite db: multi-conference, season-aware.")

# Sidebar controls
st.sidebar.header("Filters")

conf_df = get_conferences()
if conf_df.empty:
    st.error("No conferences found in DB. Make sure you ran the loaders.")
    st.stop()

conf_display = {
    f"{row['conference_key']} – {row['name']}": row["conference_key"]
    for _, row in conf_df.iterrows()
}

conf_label = st.sidebar.selectbox(
    "Conference",
    options=list(conf_display.keys()),
    index=0,
)
conference_key = conf_display[conf_label]

seasons = get_seasons(conference_key)
if not seasons:
    st.error(f"No seasons found for conference '{conference_key}'.")
    st.stop()

season_end_year = st.sidebar.selectbox(
    "Season end year", options=seasons, index=0)

teams = get_teams(conference_key, season_end_year)
team_options = ["All teams"] + teams
team_choice = st.sidebar.selectbox("Team", options=team_options, index=0)
team_slug = None if team_choice == "All teams" else team_choice

name_filter = st.sidebar.text_input(
    "Player name contains", value="").strip() or None

# Query data
df_players = get_player_profiles(
    conference_key=conference_key,
    season_end_year=season_end_year,
    team_slug=team_slug,
    name_filter=name_filter,
)

st.subheader("Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Conference", conference_key)
col2.metric("Players in query", len(df_players))
col3.metric("Teams in query",
            df_players["team_slug"].nunique() if not df_players.empty else 0)

st.markdown("---")

st.subheader("Player profiles")

if df_players.empty:
    st.info("No players match the current filters.")
else:
    # Nicely order columns
    desired_cols = [
        "player_name",
        "team_slug",
        "conference_key",
        "season_end_year",
        "class_year",
        "pos",
        "height_cm",
        "weight_kg",
        "g",
        "mp",
        "pts",
        "reb",
        "ast",
    ]
    cols = [c for c in desired_cols if c in df_players.columns]
    df_display = df_players[cols]

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )
