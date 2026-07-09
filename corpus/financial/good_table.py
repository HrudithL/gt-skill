"""Financial archetype — good example.

Source: ../../data/sp500.csv  (S&P 500 daily prices, 1950–2015)
Story:  At-a-glance monthly summary of the S&P 500 in 2015 — closing
        level, intraday range, month-over-month return, year-to-date
        return — for a reader who wants the year-in-review in one
        screen.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT, loc, style

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to the most recent full year in the dataset (2015). A single year
# keeps the narrative tight; 12 rows is the cap most readers can scan without
# the table needing scrolling or grouping.
year = df[df["date"].dt.year == 2015].copy()
year["month"] = year["date"].dt.to_period("M")

# Month-end close: take the last observation in each month rather than a mean.
# Mean smears the month and would not reconcile with the published close.
monthly = year.groupby("month").agg(
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
)

# Returns are computed on close. MoM uses prior-month close; YTD uses the
# December 2014 close so January 2015's row has a meaningful baseline.
prior_year_close = df.loc[df["date"] == "2014-12-31", "close"].iloc[0]
monthly["mom_return"] = monthly["close"].pct_change()
monthly.loc[monthly.index[0], "mom_return"] = (
    monthly["close"].iloc[0] / prior_year_close - 1
)
monthly["ytd_return"] = monthly["close"] / prior_year_close - 1

monthly = monthly.reset_index()
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
monthly = monthly[["month_label", "close", "high", "low", "mom_return", "ytd_return"]].reset_index(drop=True)

# Pre-compute index lists for the up/down coloring below. great_tables'
# tab_style takes integer row indices (not pandas boolean masks), so the
# selection lives here as a one-time list build.
mom_up = monthly.index[monthly["mom_return"] >= 0].tolist()
mom_down = monthly.index[monthly["mom_return"] < 0].tolist()
ytd_up = monthly.index[monthly["ytd_return"] >= 0].tolist()
ytd_down = monthly.index[monthly["ytd_return"] < 0].tolist()

# ---- Table -------------------------------------------------------------------
# Build the GT object up-front so each chained call is one design decision we
# can annotate.
gt = (
    GT(monthly)
    # Title carries the story; subtitle gives the data window. Splitting them
    # so the eye lands on "S&P 500" first, then the qualifier, is what
    # tab_header is for — manual newlines in a single string would not get
    # the typographic emphasis right.
    .tab_header(
        title="S&P 500 — 2015 Year in Review",
        subtitle="Month-end close, intraday range, and returns",
    )
    # Spanners group the two return columns under one label so the reader
    # parses "Return" once instead of twice. The price columns get their own
    # spanner for symmetry.
    .tab_spanner(label="Price ($)", columns=["close", "high", "low"])
    .tab_spanner(label="Return", columns=["mom_return", "ytd_return"])
    .cols_label(
        month_label="Month",
        close="Close",
        high="High",
        low="Low",
        mom_return="MoM",
        ytd_return="YTD",
    )
    # fmt_currency (not fmt_number) on price columns: it renders the $ sign,
    # thousands separator, and consistent decimals together. Reaching the
    # same effect with fmt_number requires manual string prefixing that
    # breaks under RTL locales and Accounting style.
    .fmt_currency(columns=["close", "high", "low"], currency="USD", decimals=2)
    # fmt_percent with force_sign=True: the leading + on positive months is
    # what tells the reader at a glance whether the market was up or down,
    # without them having to scan for a minus sign or compare to neighbors.
    .fmt_percent(columns=["mom_return", "ytd_return"], decimals=2, force_sign=True)
    # Color the return cells: green for positive, red for negative. Done with
    # tab_style + loc.body (not data_color) because data_color would map a
    # continuous gradient over the whole column, which is overkill — the
    # signal we want is binary up/down, not magnitude.
    .tab_style(
        style=style.text(color="#1b7837"),
        locations=loc.body(columns=["mom_return"], rows=mom_up),
    )
    .tab_style(
        style=style.text(color="#b2182b"),
        locations=loc.body(columns=["mom_return"], rows=mom_down),
    )
    .tab_style(
        style=style.text(color="#1b7837"),
        locations=loc.body(columns=["ytd_return"], rows=ytd_up),
    )
    .tab_style(
        style=style.text(color="#b2182b"),
        locations=loc.body(columns=["ytd_return"], rows=ytd_down),
    )
    # Right-align the numeric columns. Great_tables does this by default for
    # numeric dtypes, but stating it makes the intent explicit and survives
    # column-type changes during refactors.
    .cols_align(align="right", columns=["close", "high", "low", "mom_return", "ytd_return"])
    .cols_align(align="left", columns=["month_label"])
    # Source note: small, footnoted line crediting the data. Required for any
    # financial table that will be read out of context — without it the
    # reader cannot replicate or trust the numbers.
    .tab_source_note(source_note="Source: S&P 500 daily closing prices, 2015.")
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
