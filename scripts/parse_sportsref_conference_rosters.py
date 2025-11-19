from pathlib import Path
import pandas as pd

from cli_args import parse_conference_season


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def parse_height_to_cm(ht: str | None):
    if not isinstance(ht, str):
        return None
    ht = ht.strip()
    if "-" not in ht:
        return None
    feet, inches = ht.split("-", 1)
    if not (feet.isdigit() and inches.isdigit()):
        return None
    total_inches = int(feet) * 12 + int(inches)
    return round(total_inches * 2.54)


def parse_weight_to_kg(wt):
    try:
        lbs = int(str(wt).strip())
    except (ValueError, TypeError):
        return None
    return round(lbs * 0.45359237)


def find_roster_table(html_path: Path) -> pd.DataFrame:
    """
    Find roster table: needs 'Player' and ('Class' or 'Pos')
    """
    tables = pd.read_html(html_path, flavor="bs4")

    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if "player" in cols and ("class" in cols or "pos" in cols):
            return tbl

    raise ValueError(f"No roster table found in {html_path.name}")


def parse_roster_file(html_path: Path) -> pd.DataFrame:
    stem = html_path.stem           # example: "troy_2025"
    team_slug, season_str = stem.rsplit("_", 1)
    season = int(season_str)

    df = find_roster_table(html_path)

    # Rename columns
    rename_map = {}
    for col in df.columns:
        low = str(col).strip().lower()
        if low == "player":
            rename_map[col] = "player"
        elif low in ("class", "cl", "yr", "year"):
            rename_map[col] = "class_year"
        elif low in ("pos", "position"):
            rename_map[col] = "pos"
        elif low in ("ht", "height", "hgt"):
            rename_map[col] = "height_raw"
        elif low in ("wt", "weight"):
            rename_map[col] = "weight_lbs"

    df = df.rename(columns=rename_map)

    if "player" not in df.columns:
        raise ValueError(f"'Player' column missing in {html_path.name}")

    keep_cols = ["player"]
    for col in ("class_year", "pos", "height_raw", "weight_lbs"):
        if col in df.columns:
            keep_cols.append(col)

    df = df[keep_cols].copy()

    # Metadata
    df["team_slug"] = team_slug
    df["season_end_year"] = season

    # Clean + conversions
    df["player"] = df["player"].astype(str).str.strip()
    df = df[df["player"] != ""]

    df["height_cm"] = df.get("height_raw", pd.Series(
        [None] * len(df))).apply(parse_height_to_cm)
    df["weight_kg"] = df.get("weight_lbs", pd.Series(
        [None] * len(df))).apply(parse_weight_to_kg)

    return df


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    conf, season_end_year = parse_conference_season()

    project_root = Path(__file__).resolve().parents[1]
    season_label = f"{season_end_year - 1}-{season_end_year}"

    raw_dir = (
        project_root /
        "ncaa-analytics" /
        "data_raw" /
        conf.data_subdir /
        season_label
    )

    out_dir = (
        project_root /
        "ncaa-analytics" /
        "data_intermediate" /
        conf.data_subdir /
        season_label
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Conference: {conf.name} ({conf.key})")
    print(f"Season end year: {season_end_year}")
    print(f"Reading from: {raw_dir}")
    print(f"Writing to:   {out_dir}\n")

    all_rows = []

    for html_path in sorted(raw_dir.glob(f"*_{season_end_year}.html")):
        print(f"Parsing roster from {html_path.name} ...")
        try:
            df_team = parse_roster_file(html_path)
            print(f"  -> parsed {len(df_team)} rows")
            all_rows.append(df_team)

            out_csv = out_dir / f"{html_path.stem}_roster.csv"
            df_team.to_csv(out_csv, index=False)

        except Exception as e:
            print(f"  !! ERROR on {html_path.name}: {e}")

    if not all_rows:
        print("No roster data parsed.")
        return

    final_df = pd.concat(all_rows, ignore_index=True)
    combined_csv = out_dir / \
        f"{conf.key}_{season_end_year}_roster_all_teams.csv"
    final_df.to_csv(combined_csv, index=False)

    print(
        f"\nWrote combined roster CSV: {combined_csv} ({len(final_df)} rows)")


if __name__ == "__main__":
    main()
