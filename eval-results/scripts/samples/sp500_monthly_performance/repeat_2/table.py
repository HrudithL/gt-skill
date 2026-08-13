import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])
df_raw = df_raw.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]

# Create year-month identifier and aggregate
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Group by month and calculate metrics
monthly_data = []
for period, group in df_raw.groupby("year_month"):
    # Opening price (first day of month)
    opening = group.iloc[0]["open"]
    # Closing price (last day of month)
    closing = group.iloc[-1]["close"]
    # Percent change
    pct_change = (closing - opening) / opening
    # Average daily volume
    avg_volume = group["volume"].mean()
    # Highest single-day gain (max high - prior close, but we use daily change proxy)
    # For each day, calculate high - open (intraday gain potential)
    daily_gains = group["high"] - group["open"]
    max_gain = daily_gains.max()
    # Highest single-day loss (min low - prior open)
    daily_losses = group["low"] - group["open"]
    max_loss = daily_losses.min()

    monthly_data.append({
        "Month": period.strftime("%b %Y"),
        "Month_Sort": period,
        "Open": opening,
        "Close": closing,
        "Pct_Change": pct_change,
        "Avg_Volume": avg_volume,
        "Max_Gain": max_gain,
        "Max_Loss": max_loss,
    })

df = pd.DataFrame(monthly_data)
df = df.sort_values("Month_Sort").reset_index(drop=True)
df = df.drop("Month_Sort", axis=1)

# Step 2: Organize columns and create table
gt = (
    GT(df, rowname_col="Month")
    .cols_width(cases={
        "Open": "110px",
        "Close": "110px",
        "Pct_Change": "100px",
        "Avg_Volume": "120px",
        "Max_Gain": "90px",
        "Max_Loss": "90px",
    })
    # Step 3 & 5: Formatting
    .fmt_number(columns=["Open", "Close"], decimals=2, use_seps=True)
    .fmt_percent(columns=["Pct_Change"], decimals=1, force_sign=True)
    .fmt_number(columns=["Avg_Volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["Max_Gain", "Max_Loss"], decimals=2)
    .sub_missing(columns=["Open", "Close", "Pct_Change", "Avg_Volume", "Max_Gain", "Max_Loss"], missing_text="—")
    # Column label formatting
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles and annotations
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015"
    )
    .tab_source_note("Monthly metrics: opening/closing prices, percent change for the month, average daily trading volume, and the highest intraday gain and loss observed.")
    .tab_source_note("Source: S&P 500 historical data (sp500.csv)")
)

# Step 3: Color fills for key performance metrics
# Percent change (neutral magnitude)
gt = heatmap(gt, "Pct_Change", kind="sequential", hue="neutral")
# Max gain (positive/good direction)
gt = heatmap(gt, "Max_Gain", kind="sequential", hue="positive")
# Max loss (warning/bad direction)
gt = heatmap(gt, "Max_Loss", kind="sequential", hue="warning")

# Step 4: Heading band
gt = band(gt)

# Step 5: Small color polish
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Frame
gt = frame(gt)

finalize(gt, "table.png")
