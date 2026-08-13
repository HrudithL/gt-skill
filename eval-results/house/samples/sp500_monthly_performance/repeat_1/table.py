import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read and prepare data
df = pd.read_csv("sp500.csv", parse_dates=["date"])
df = df[(df["date"] >= "2010-01-01") & (df["date"] <= "2015-12-31")].copy()
df = df.sort_values("date")

# Compute monthly summary statistics
df["year_month"] = df["date"].dt.to_period("M")
monthly = df.groupby("year_month", observed=True).agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
    volume=("volume", "sum")
).reset_index()

# Rename for display
monthly.rename(columns={"year_month": "month"}, inplace=True)

# Calculate percent change and daily gains/losses
monthly["pct_change"] = (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]

# For daily gains and losses, re-group by month and compute
daily_movements = []
for period, group in df.groupby("year_month", observed=True):
    group = group.sort_values("date")
    # Daily gain/loss (highest/lowest relative change within the month)
    group["daily_change"] = group["close"] - group["open"]

    max_gain = group["daily_change"].max()
    max_loss = group["daily_change"].min()  # most negative = biggest loss

    daily_movements.append({
        "month": period,
        "highest_daily_gain": max_gain,
        "highest_daily_loss": max_loss,
    })

daily_df = pd.DataFrame(daily_movements)
monthly = monthly.merge(daily_df, on="month", how="left")

# Convert period to string for display
monthly["month"] = monthly["month"].astype(str)

# Reorder columns
monthly = monthly[[
    "month", "open_price", "close_price", "pct_change",
    "volume", "highest_daily_gain", "highest_daily_loss"
]]

# Build the table
gt = GT(monthly, rowname_col="month")
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle=md("2010–2015: Opening price, closing price, monthly return, average daily volume, and daily extremes"),
)

# Format columns
gt = gt.fmt_number(columns="open_price", decimals=2)
gt = gt.fmt_number(columns="close_price", decimals=2)
gt = gt.fmt_percent(columns="pct_change", decimals=2, force_sign=True)
gt = gt.fmt_number(columns="volume", decimals=0, use_seps=True)
gt = gt.fmt_number(columns="highest_daily_gain", decimals=2)
gt = gt.fmt_number(columns="highest_daily_loss", decimals=2)

# Apply humanized labels
gt = humanize_labels(
    gt,
    monthly,
    overrides={
        "open_price": "Opening Price",
        "close_price": "Closing Price",
        "pct_change": "Monthly Return %",
        "volume": "Total Volume",
        "highest_daily_gain": "Highest Daily Gain",
        "highest_daily_loss": "Highest Daily Loss",
    },
)

# Column widths
gt = gt.cols_width(
    cases={
        "month": "100px",
        "open_price": "120px",
        "close_price": "120px",
        "pct_change": "120px",
        "volume": "140px",
        "highest_daily_gain": "130px",
        "highest_daily_loss": "130px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Heatmap the percent change (diverging measure)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Style
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes
gt = gt.tab_source_note(
    source_note="Monthly Return % is calculated as (closing price − opening price) / opening price. Highest Daily Gain and Loss are the largest single-day price movements within each month."
)
gt = gt.tab_source_note(source_note="Source: S&P 500 daily price data, 2010–2015.")

# Finalize
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
