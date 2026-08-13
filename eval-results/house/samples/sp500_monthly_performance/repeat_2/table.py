import pandas as pd
import numpy as np
from great_tables import GT, loc, style, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("sp500.csv", parse_dates=["date"])

# Filter to 2010-2015
df_filtered = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df_filtered = df_filtered.sort_values("date").reset_index(drop=True)

# Build monthly summary
monthly_data = []
for year_month, group in df_filtered.groupby(df_filtered["date"].dt.to_period("M")):
    month_df = group.reset_index(drop=True)

    first_day = month_df["date"].min()
    last_day = month_df["date"].max()
    opening = month_df.iloc[0]["open"]
    closing = month_df.iloc[-1]["close"]
    pct_change = ((closing - opening) / opening) * 100
    avg_volume = month_df["volume"].mean()

    # Daily gains/losses within the month
    month_df["daily_change"] = month_df["close"] - month_df["open"]
    highest_gain = month_df["daily_change"].max()
    highest_loss = month_df["daily_change"].min()

    monthly_data.append({
        "month": first_day.strftime("%b %Y"),
        "opening": opening,
        "closing": closing,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "highest_gain": highest_gain,
        "highest_loss": highest_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Build table
gt = (
    GT(monthly_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle=md("Opening price, closing price, percent change, average daily volume, and intramonth high/low by day — 2010–2015"),
    )
    .fmt_number(columns="opening", decimals=2, use_seps=False)
    .fmt_number(columns="closing", decimals=2, use_seps=False)
    .fmt_number(columns="pct_change", decimals=2, use_seps=False, pattern="{x}%", force_sign=True)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_number(columns="highest_gain", decimals=2, use_seps=False, force_sign=True)
    .fmt_number(columns="highest_loss", decimals=2, use_seps=False, force_sign=True)
)

gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        "opening": "Opening",
        "closing": "Closing",
        "pct_change": "% Change",
        "avg_volume": "Avg Volume",
        "highest_gain": "Highest Gain",
        "highest_loss": "Highest Loss",
    },
)

gt = gt.cols_width(
    cases={
        "month": "100px",
        "opening": "100px",
        "closing": "100px",
        "pct_change": "100px",
        "avg_volume": "120px",
        "highest_gain": "110px",
        "highest_loss": "110px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Heatmap: percent change (diverging)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Heatmap: average volume (sequential)
gt = heatmap(gt, "avg_volume", kind="sequential", hue="neutral")

# Band and polish
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Percent change is calculated as (closing - opening) / opening. Highest gain and loss represent the maximum and minimum daily changes (close - open) within each month."
    )
    .tab_source_note(source_note="Source: S&P 500 historical price data.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
