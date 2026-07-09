"""Ranking archetype — good example.

Source: ../../data/gtcars.csv  (47 high-performance cars, with msrp,
        horsepower, country of origin, etc.)
Story:  "Most powerful production cars in the dataset" — a top-10
        ranking by horsepower, with model, country, drivetrain, MSRP.
        The reader is a buff who wants the leaderboard at a glance and
        the leader visually called out.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT, loc, style

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

# Compose the human-readable model label from manufacturer + model. Two
# separate columns would force the reader's eye to combine them; a single
# `Car` column lets the row breathe.
df["car"] = df["mfr"] + " " + df["model"]

# Sort by hp descending and take the top 10. The point of a ranking table is
# the leaderboard — showing all 47 cars buries the leaders.
top = (
    df.sort_values("hp", ascending=False)
      .head(10)
      .reset_index(drop=True)
)
top["rank"] = top.index + 1  # 1-based rank column; the eye expects #1 not #0.

top = top[["rank", "car", "year", "ctry_origin", "hp", "trq", "drivetrain", "msrp"]]

# ---- Table -------------------------------------------------------------------
gt = (
    GT(top)
    .tab_header(
        title="Top 10 by Horsepower",
        subtitle="Production cars in the gtcars dataset, ranked by peak HP",
    )
    .cols_label(
        rank="#",
        car="Car",
        year="Year",
        ctry_origin="Country",
        hp="HP",
        trq="Torque (lb-ft)",
        drivetrain="Drive",
        msrp="MSRP",
    )
    # MSRP as currency with no decimals — vehicle prices are quoted in whole
    # dollars in the trade press; cents would imply false precision.
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    # HP and torque as integers with thousands separators — these are spec
    # numbers, not measurements with uncertainty.
    .fmt_integer(columns=["hp", "trq"])
    # Year as a plain integer with no thousands separator — `2,017` is wrong
    # for years; `fmt_integer(use_seps=False)` is the documented escape.
    .fmt_integer(columns=["year"], use_seps=False)
    # Bold the rank column so the row index pops, then highlight the #1 row
    # so the eye lands on the leader first. tab_style with loc.body lets us
    # scope the highlight to the single top row by its integer index.
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["rank"]),
    )
    .tab_style(
        style=style.fill(color="#fff4d6"),  # warm pale yellow — "podium" tint
        locations=loc.body(rows=[0]),
    )
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["car", "hp"], rows=[0]),
    )
    # Right-align everything numeric; left-align Car and Country since text
    # columns read more naturally left-aligned.
    .cols_align(align="left", columns=["car", "ctry_origin", "drivetrain"])
    .cols_align(align="right", columns=["rank", "year", "hp", "trq", "msrp"])
    .tab_source_note(
        source_note="Source: gtcars dataset (Posit / great_tables sample data)."
    )
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
