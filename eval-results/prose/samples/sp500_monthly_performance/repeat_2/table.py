"""S&P 500 Monthly Performance (2010-2015)

Data: sp500.csv (S&P 500 daily prices)
Story: Monthly summary across 2010-2015 with opening price, closing price,
       percent change, average daily volume, and highest single-day gain/loss
       within each month.
"""
import numpy as np
import pandas as pd
from great_tables import GT

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Get the last trading day of 2009 for baseline
last_2009 = df[df["date"].dt.year == 2009].iloc[-1]["close"]

# Restrict to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Create a month period column for grouping
df["month"] = df["date"].dt.to_period("M")

# Compute intra-day changes (high-open and low-open represent intraday range relative to open)
df["daily_gain"] = (df["high"] - df["open"]) / df["open"]
df["daily_loss"] = (df["low"] - df["open"]) / df["open"]

# Aggregate by month
monthly = df.groupby("month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    high_daily_gain=("daily_gain", "max"),
    low_daily_loss=("daily_loss", "min"),
    avg_volume=("volume", "mean"),
)

# Compute month-over-month percent change from open to close
monthly["pct_change"] = (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]

# For January 2010, use the year-end 2009 close as baseline
monthly.loc[monthly.index[0], "pct_change"] = (
    monthly["close_price"].iloc[0] / last_2009 - 1
)

# Reset index and format month label
monthly = monthly.reset_index()
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

# Select and order columns
monthly = monthly[[
    "month_label", "open_price", "close_price", "pct_change",
    "avg_volume", "high_daily_gain", "low_daily_loss"
]].reset_index(drop=True)

# Compute shared domain for the two signed measures (daily gain/loss)
# These represent opposite ends of the same daily volatility measure
day_extremes = np.concatenate([
    monthly["high_daily_gain"].to_numpy(),
    np.abs(monthly["low_daily_loss"].to_numpy())
])
day_m = float(np.nanmax(day_extremes))

gt = (
    GT(monthly)
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="Opening and closing prices, monthly return, trading volume, and daily extremes (2010–2015)",
    )
    .tab_spanner(label="Price ($)", columns=["open_price", "close_price"])
    .tab_spanner(label="Daily Range", columns=["high_daily_gain", "low_daily_loss"])
    .cols_label(
        month_label="Month",
        open_price="Open",
        close_price="Close",
        pct_change="Monthly %",
        avg_volume="Avg Volume",
        high_daily_gain="Highest Gain",
        low_daily_loss="Lowest Loss",
    )
    # Format prices
    .fmt_currency(columns=["open_price", "close_price"], currency="USD", decimals=2)
    # Format percent change with force_sign so +/- is at-a-glance
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    # Format daily gains/losses as percent with force_sign
    .fmt_percent(columns=["high_daily_gain", "low_daily_loss"], decimals=2, force_sign=True)
    # Format volume (millions for readability)
    .fmt_number(columns=["avg_volume"], decimals=0)
    # Color the monthly return (one signed measure)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-0.10, 0.10],
        na_color="#808080",
        truncate=False,
    )
    # Color the daily extremes as a related pair sharing one domain and palette
    .data_color(
        columns=["high_daily_gain", "low_daily_loss"],
        palette="PuOr",
        domain=[-day_m, day_m],
        na_color="#808080",
        truncate=False,
    )
    # Alignment
    .cols_align(align="left", columns=["month_label"])
    .cols_align(align="right", columns=["open_price", "close_price", "pct_change",
                                        "avg_volume", "high_daily_gain", "low_daily_loss"])
    .tab_source_note(
        source_note="Source: S&P 500 daily closing prices, 2010–2015. Daily gains/losses are intraday ranges relative to opening price."
    )
)

gt.gtsave("table.png")
