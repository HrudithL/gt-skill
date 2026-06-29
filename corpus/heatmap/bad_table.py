"""Heatmap / data-cell-styling archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *No `data_color()` at all — raw percentages dumped as text.*
    A bonus anti-pattern: when color IS applied to one column, it's a
    rainbow palette on a signed quantity, which has no perceptual
    ordering and is the textbook "do not use" choice for any
    quantitative variable. The reader cannot spot patterns without
    reading every cell.

Same source CSV as good_table.py (../../data/towny.csv).
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))
import gtskill_chrome  # noqa: F401

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "towny.csv")
change_cols = [
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]
top = df.nlargest(15, "population_2021")[["name", "population_2021"] + change_cols]

# BAD: no data_color on the growth columns — five columns of bare percentages
# defeat the heatmap archetype entirely. As a bonus anti-pattern, ONE column
# gets a rainbow palette, which is perceptually non-monotonic on a signed
# variable (jet is the canonical "do not use this on quantitative data").
(
    GT(top)
    .fmt_number(columns=change_cols, decimals=4)
    .data_color(
        columns=["pop_change_2016_2021_pct"],
        palette=["red", "orange", "yellow", "green", "blue", "purple"],
    )
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
