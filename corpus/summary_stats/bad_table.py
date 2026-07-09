"""Summary statistics archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *No aggregation, no grouping, no totals — raw transactions.* The
    script prints the first 25 individual pizza orders verbatim,
    leaving the reader to do every sum, count, and group-by themselves.
    The whole point of a summary table — to summarize — is missing.

Same source CSV as good_table.py (../../data/pizzaplace.csv).
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "pizzaplace.csv")

# BAD: 25 raw transactions, no aggregation, no grouping, no totals. Compare
# to good_table.py which collapses 49,574 rows to 14 grouped rows with
# subtotals and a grand total at the bottom.
sample = df.head(25)

(
    GT(sample)
    .fmt_number(columns=["price"], decimals=2)
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
