"""Heatmap / data-cell-styling archetype — good example.

Source: ../../data/towny.csv  (414 Ontario municipalities; population
        and growth across five Census windows from 1996 to 2021)
Story:  Twenty-five years of growth in Ontario's 15 largest cities,
        rendered as a heatmap so the reader spots boom/bust patterns at
        a glance without reading the numbers.

Gradient convention (per spec §13 Q1, decided in advance):
    diverging palette centered at 0%, red = decline, green = growth.
    A diverging scale is chosen because growth-rate data is intrinsically
    signed; a sequential scale would conflate "no change" with one of
    the extremes.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT, html

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "towny.csv")

# 15 largest cities by 2021 population. Restricting to the top end keeps the
# heatmap readable; with all 414 municipalities the grid is unreadable and
# the eye cannot detect patterns.
change_cols = [
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]
top = (
    df.nlargest(15, "population_2021")
      .loc[:, ["name", "population_2021"] + change_cols]
      .reset_index(drop=True)
)

# ---- Table -------------------------------------------------------------------
# Bound the color scale symmetrically around zero so the white midpoint is
# always "no change", not the column mean. Without this, a column with all
# positive values would map 0% to red (which is misleading).
abs_max = max(abs(top[change_cols].min().min()),
              abs(top[change_cols].max().max()))

gt = (
    GT(top)
    .tab_header(
        title="Population growth in Ontario's 15 largest cities",
        subtitle="Five-year percent change across each Census window, 1996–2021",
    )
    .cols_label(
        name="City",
        population_2021="2021 pop.",
        pop_change_1996_2001_pct="1996–2001",
        pop_change_2001_2006_pct="2001–2006",
        pop_change_2006_2011_pct="2006–2011",
        pop_change_2011_2016_pct="2011–2016",
        pop_change_2016_2021_pct="2016–2021",
    )
    .tab_spanner(label="Inter-Census growth", columns=change_cols)
    .fmt_integer(columns=["population_2021"])
    # Percent labels for each cell at one decimal — the underlying precision
    # of the Statistics Canada source. force_sign so the eye gets the
    # direction from the text too, not just from the color (color-blind
    # readers need the redundant signal).
    .fmt_percent(columns=change_cols, decimals=1, force_sign=True)
    # The heatmap itself. RdYlGn diverging palette: red = decline, green =
    # growth, yellow/white = near zero. domain anchored symmetrically on
    # ±abs_max so 0% always maps to the midpoint regardless of the values
    # in the data — this is the correctness invariant for diverging color.
    .data_color(
        columns=change_cols,
        palette=["#b2182b", "#ef8a62", "#fddbc7", "#f7f7f7",
                 "#d9f0d3", "#7fbf7b", "#1b7837"],
        domain=[-abs_max, abs_max],
    )
    .cols_align(align="left", columns=["name"])
    .cols_align(align="right", columns=["population_2021"] + change_cols)
    .tab_source_note(
        source_note=html(
            "Source: Statistics Canada Census of Population, 1996–2021, "
            "via the <code>towny</code> dataset (Posit / great_tables sample data). "
            "Color scale: red = decline, green = growth, midpoint at 0%."
        )
    )
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
