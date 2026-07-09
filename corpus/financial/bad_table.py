"""Financial archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *Currency data formatted as raw numbers.* No $ sign, no signed
    deltas on percentage changes, no up/down coloring. Reader cannot
    tell at a glance whether a row represents money, an index level,
    or an arbitrary count, and cannot tell whether the market was up
    or down without doing the subtraction themselves.

Same source CSV as good_table.py (../../data/sp500.csv) so the judge is
comparing presentation, not data.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "sp500.csv", parse_dates=["date"]).sort_values("date")
year = df[df["date"].dt.year == 2015].copy()
year["month"] = year["date"].dt.to_period("M")
monthly = year.groupby("month").agg(
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
)
prior_year_close = df.loc[df["date"] == "2014-12-31", "close"].iloc[0]
monthly["mom_return"] = monthly["close"].pct_change()
monthly.loc[monthly.index[0], "mom_return"] = (
    monthly["close"].iloc[0] / prior_year_close - 1
)
monthly["ytd_return"] = monthly["close"] / prior_year_close - 1
monthly = monthly.reset_index()
monthly["month"] = monthly["month"].astype(str)

# BAD: fmt_number on currency columns. No $ symbol, no thousands separator
# choice baked in — and the same formatter is reused on percentages, which
# show up as decimal fractions like 0.013 instead of 1.30%. Compare to
# good_table.py which uses fmt_currency on prices and fmt_percent with
# force_sign=True on returns.
#
# BAD: no spanners, no header, no source note, no column re-labeling. The
# raw dataframe column names (`mom_return`, `ytd_return`) leak through.
#
# BAD: no row coloring on returns. The reader has to scan for minus signs.
(
    GT(monthly)
    .fmt_number(columns=["close", "high", "low", "mom_return", "ytd_return"], decimals=4)
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
