import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Calculate monthly metrics
monthly_data = []

for year in range(2010, 2016):
    for month in range(1, 13):
        month_df = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]

        if len(month_df) == 0:
            continue

        # Sort by date to get opening and closing prices
        month_df = month_df.sort_values("date")

        open_price = month_df.iloc[0]["open"]
        close_price = month_df.iloc[-1]["close"]
        pct_change = ((close_price - open_price) / open_price) * 100

        # Average daily volume
        avg_volume = month_df["volume"].mean()

        # Daily gains/losses within the month
        month_df["daily_change"] = month_df["close"] - month_df["open"]
        best_day = month_df["daily_change"].max()
        worst_day = month_df["daily_change"].min()

        # Format month label
        month_label = datetime(year, month, 1).strftime("%b %Y")

        monthly_data.append({
            "month": month_label,
            "open": open_price,
            "close": close_price,
            "pct_change": pct_change,
            "avg_volume": avg_volume,
            "best_day_gain": best_day,
            "worst_day_loss": worst_day,
        })

# Create DataFrame
summary_df = pd.DataFrame(monthly_data)

# Create GT object with month as stub
gt = GT(summary_df, rowname_col="month")

# Apply title and subtitles
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010 through 2015"
)

# Format columns
gt = gt.fmt_currency(columns=["open", "close", "best_day_gain", "worst_day_loss"], decimals=2)
gt = gt.fmt_number(columns="avg_volume", decimals=0)
gt = gt.fmt_percent(columns="pct_change", decimals=2, scale_values=False)

# Apply source notes
gt = gt.tab_source_note(
    source_note="Monthly summaries include opening and closing prices, percent change, average daily volume, and the highest single-day gain and loss within each month."
)
gt = gt.tab_source_note(
    source_note="Source: S&P 500 historical price data."
)

# Apply humanized labels with overrides
gt = humanize_labels(gt, summary_df, overrides={
    "open": "Opening Price",
    "close": "Closing Price",
    "pct_change": "Monthly % Change",
    "avg_volume": "Avg Daily Volume",
    "best_day_gain": "Best Day Gain",
    "worst_day_loss": "Worst Day Loss",
})

# Apply spanner for daily extremes
gt = gt.tab_spanner(
    label="Daily Extremes",
    columns=["best_day_gain", "worst_day_loss"]
)

# Add vertical divider before the spanner
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="avg_volume")
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="avg_volume")
)

# Apply missing value substitution
gt = gt.sub_missing(columns=["open", "close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"], missing_text="—")

# Set column widths
gt = gt.cols_width(cases={
    "month": "120px",
    "open": "110px",
    "close": "110px",
    "pct_change": "120px",
    "avg_volume": "130px",
    "best_day_gain": "120px",
    "worst_day_loss": "120px",
})

# Apply padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply house format styling
gt = frame(gt)
gt = hairlines(gt)
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)

# Apply color to percent change (diverging heatmap)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Finalize and save
finalize(gt, path="table.png")
