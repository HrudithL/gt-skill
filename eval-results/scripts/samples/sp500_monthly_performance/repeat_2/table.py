import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import band, frame, heatmap, stripe, stub_tint, finalize

# Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Calculate daily high-low gain/loss for each day
df_raw["daily_gain"] = df_raw["high"] - df_raw["open"]
df_raw["daily_loss"] = df_raw["low"] - df_raw["open"]

# Extract year-month for grouping
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Aggregate by month
monthly = df_raw.groupby("year_month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    avg_volume=("volume", "mean"),
    highest_gain=("daily_gain", "max"),
    highest_loss=("daily_loss", "min"),
).reset_index()

# Calculate percent change
monthly["pct_change"] = ((monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]) * 100

# Filter to 2010-2015
monthly["year"] = monthly["year_month"].dt.year
df = monthly[(monthly["year"] >= 2010) & (monthly["year"] <= 2015)].copy()
df = df.drop("year", axis=1)

# Create month-year label for display
df["month_label"] = df["year_month"].astype(str)

# Reorder columns
df = df[["month_label", "open_price", "close_price", "pct_change", "avg_volume", "highest_gain", "highest_loss"]]

# Build the table
gt = (
    GT(df, rowname_col="month_label")
    .cols_label(
        open_price="Opening Price",
        close_price="Closing Price",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        highest_gain="Highest Daily Gain",
        highest_loss="Highest Daily Loss",
    )
    .cols_width(
        cases={
            "open_price": "110px",
            "close_price": "120px",
            "pct_change": "95px",
            "avg_volume": "135px",
            "highest_gain": "130px",
            "highest_loss": "130px",
        }
    )
    .fmt_number(columns=["open_price", "close_price"], decimals=2, use_seps=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["highest_gain", "highest_loss"], decimals=2, use_seps=False)
    .fmt_percent(columns="pct_change", decimals=2, scale_values=False, force_sign=True)
    .sub_missing(columns=["open_price", "close_price", "pct_change", "avg_volume", "highest_gain", "highest_loss"], missing_text="—")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="12px",
        column_labels_padding="12px",
        column_labels_padding_horizontal="8px",
        data_row_padding="8px",
        data_row_padding_horizontal="8px",
        source_notes_padding="12px",
    )
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening and closing prices, percent change, average daily volume, and daily gain/loss extremes",
    )
    .tab_source_note(source_note="Percent change is calculated as (closing price − opening price) ÷ opening price × 100. Highest daily gain and loss represent the intraday high and low relative to each day's opening price, within each month.")
    .tab_source_note(source_note="Source: sp500.csv")
)

# Apply heatmap to percent change (the hero measure)
gt = heatmap(gt, columns=["pct_change"], kind="diverging", hue="default")

# Apply branding styling
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Apply frame
gt = frame(gt)

# Finalize and render
finalize(gt, "table.png")
