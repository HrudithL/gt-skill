"""Ranking archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *Unsorted dump of all rows with every column kept.* No rank
    column, no leader emphasis, no column hiding, no formatting. The
    reader cannot tell at a glance which car wins on horsepower
    without scanning all 47 values.

Same source CSV as good_table.py (../../data/gtcars.csv).
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

# BAD: all 47 rows, all 15 columns, in CSV order. Compare to good_table.py
# which sorts by hp descending, hides irrelevant columns, and surfaces the
# top 10 with a # column.
(
    GT(df)
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
