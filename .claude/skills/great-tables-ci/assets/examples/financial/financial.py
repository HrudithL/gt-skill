"""Financial archetype — distilled reference example.

Data: data/sp500.csv  (S&P 500 daily prices, 1950–2015)
Story: At-a-glance monthly summary of the S&P 500 in 2015 — closing
       level, intraday range, month-over-month return, year-to-date
       return.
"""
import numpy as np
import pandas as pd
from great_tables import GT

df = pd.read_csv("data/sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to the most recent full year. Twelve rows is the cap most readers
# can scan without scrolling or grouping.
year = df[df["date"].dt.year == 2015].copy()
year["month"] = year["date"].dt.to_period("M")

# Month-end close: last observation in the month, not a mean (mean smears
# the month and would not reconcile with the published close).
monthly = year.groupby("month").agg(
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
)

# Use the prior-year close as the baseline so January's MoM is meaningful
# (and YTD has an anchor).
prior_year_close = df.loc[df["date"] == "2014-12-31", "close"].iloc[0]
monthly["mom_return"] = monthly["close"].pct_change()
monthly.loc[monthly.index[0], "mom_return"] = (
    monthly["close"].iloc[0] / prior_year_close - 1
)
monthly["ytd_return"] = monthly["close"] / prior_year_close - 1
monthly = monthly.reset_index()
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
monthly = monthly[["month_label", "close", "high", "low", "mom_return", "ytd_return"]].reset_index(drop=True)

# Two signed measures (MoM and YTD return) — each is its own diverging Big
# Color treatment (big_color/diverging_fill.md), sharing ONE symmetric domain
# ACROSS BOTH columns so a MoM swing and a YTD swing of equal magnitude render
# at equal saturation, not two independently-scaled columns.
ret_m = float(np.nanmax(np.abs(monthly[["mom_return", "ytd_return"]].to_numpy())))

(
    GT(monthly)
    .tab_header(
        title="S&P 500 — 2015 Year in Review",
        subtitle="Month-end close, intraday range, and returns",
    )
    # Spanners group the columns under one label so the reader parses "Return"
    # once instead of twice.
    .tab_spanner(label="Price ($)", columns=["close", "high", "low"])
    .tab_spanner(label="Return", columns=["mom_return", "ytd_return"])
    .cols_label(
        month_label="Month", close="Close", high="High", low="Low",
        mom_return="MoM", ytd_return="YTD",
    )
    # fmt_currency on prices — renders the $, thousands separator, and decimals
    # as one locale-aware unit. fmt_number + a manual prefix breaks under RTL.
    .fmt_currency(columns=["close", "high", "low"], currency="USD", decimals=2)
    # force_sign=True so the leading + is the at-a-glance up/down signal.
    .fmt_percent(columns=["mom_return", "ytd_return"], decimals=2, force_sign=True)
    # Diverging RdYlGn fill, per big_color/diverging_fill.md: positive=good is
    # the default orientation for a stock return (no reverse=True). Both
    # columns share ONE domain/palette since they're the SAME measure
    # (return) reported at two different windows, not two separate measures.
    .data_color(
        columns=["mom_return", "ytd_return"],
        palette="RdYlGn",
        domain=[-ret_m, ret_m],
        na_color="#808080",
        truncate=False,
    )
    .cols_align(align="right", columns=["close", "high", "low", "mom_return", "ytd_return"])
    .cols_align(align="left", columns=["month_label"])
    .tab_source_note(source_note="Source: S&P 500 daily closing prices, 2015.")
)
