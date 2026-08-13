import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("sp500.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
df_range = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df_range["year_month"] = df_range["date"].dt.to_period("M")

# Compute monthly summaries
monthly_summaries = []
for period, group_data in df_range.groupby("year_month"):
    group_data = group_data.sort_values("date")
    open_price = group_data["open"].iloc[0]
    close_price = group_data["close"].iloc[-1]
    pct_change = (close_price - open_price) / open_price
    avg_volume = group_data["volume"].mean()

    # Daily gains/losses within the month
    daily_changes = group_data["close"].diff()
    max_gain = daily_changes.max()
    max_loss = daily_changes.min()

    monthly_summaries.append({
        "month": period,
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "max_gain": max_gain,
        "max_loss": max_loss,
    })

monthly_df = pd.DataFrame(monthly_summaries)
monthly_df = monthly_df.sort_values("month").reset_index(drop=True)

# Format month as "Mon YYYY"
monthly_df["month_label"] = monthly_df["month"].dt.strftime("%b %Y")

# Reorder columns for display
display_df = monthly_df[["month_label", "open", "close", "pct_change", "avg_volume", "max_gain", "max_loss"]].copy()
display_df.columns = ["month", "open", "close", "pct_change", "avg_volume", "max_gain", "max_loss"]

gt = (
    GT(display_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Monthly opening price, closing price, percent change, average daily volume, and intra-month daily extremes (2010–2015)"),
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="open", decimals=2, use_seps=False)
    .fmt_number(columns="close", decimals=2, use_seps=False)
    .fmt_percent(columns="pct_change", decimals=2, force_sign=True, scale_values=False)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_number(columns="max_gain", decimals=2, force_sign=True)
    .fmt_number(columns="max_loss", decimals=2, force_sign=True)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "pct_change": "Pct Change",
        "avg_volume": "Avg Daily Volume",
        "max_gain": "Max Daily Gain",
        "max_loss": "Max Daily Loss",
    },
)

gt = gt.cols_width(
    cases={
        "month": "100px",
        "open": "90px",
        "close": "90px",
        "pct_change": "100px",
        "avg_volume": "130px",
        "max_gain": "100px",
        "max_loss": "100px",
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

# Color the percent change column with diverging palette
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = (
    gt
    .tab_source_note(
        source_note="Pct Change is the percent change from opening to closing price each month. Max Daily Gain/Loss represent the largest single-day price movement (close-to-close) within each month."
    )
    .tab_source_note(source_note="Source: S&P 500 historical daily data.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
