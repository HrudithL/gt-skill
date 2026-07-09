"""Time-series archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *No temporal aggregation, no ordering, raw integer month codes.*
    The script dumps 153 daily rows in whatever order the CSV stored
    them, prints Month as `5`/`6`/`7`, and gives the reader no trend,
    no monthly grouping, and no way to scan summer 1973 as a sequence.

Same source CSV as good_table.py (../../data/airquality.csv).
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "airquality.csv")

# BAD: take the first 20 rows verbatim — no aggregation, no ordering by date.
# Compare to good_table.py which aggregates to 5 monthly rows so the reader
# sees the season at a glance.
sample = df.head(20)

# BAD: raw numeric Month leaks through. fmt_number on a categorical column.
# No header, no labels, no source note, no trend, no grouping.
(
    GT(sample)
    .fmt_number(columns=["Ozone", "Solar_R", "Wind"], decimals=2)
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
