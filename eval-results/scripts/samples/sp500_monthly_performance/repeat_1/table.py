import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Load and prepare data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Filter for 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]

# Sort by date
df_raw = df_raw.sort_values("date").reset_index(drop=True)

# Calculate daily gain/loss for each day
df_raw["daily_gain"] = df_raw["high"] - df_raw["open"]
df_raw["daily_loss"] = df_raw["open"] - df_raw["low"]

# Extract year and month
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Group by month
monthly_data = []
for period, group in df_raw.groupby("year_month"):
    month_str = str(period)  # Format: "2010-01"

    opening_price = group.iloc[0]["open"]  # First day's opening
    closing_price = group.iloc[-1]["close"]  # Last day's closing
    pct_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = group["volume"].mean()
    best_day_gain = group["daily_gain"].max()
    worst_day_loss = group["daily_loss"].max()  # Max loss within the month

    monthly_data.append({
        "month": month_str,
        "open": opening_price,
        "close": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_daily_volume,
        "best_gain": best_day_gain,
        "worst_loss": worst_day_loss,
    })

df = pd.DataFrame(monthly_data)

# Build the table
gt = (
    GT(df, rowname_col="month")
    .fmt_number(columns=["open", "close"], decimals=2, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=2, scale_values=False, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["best_gain", "worst_loss"], decimals=2)
    .cols_label(
        open="Opening Price",
        close="Closing Price",
        pct_change="Monthly % Change",
        avg_volume="Avg Daily Volume",
        best_gain="Best Day Gain",
        worst_loss="Worst Day Loss",
    )
    .cols_width(cases={
        "month": "100px",
        "open": "120px",
        "close": "120px",
        "pct_change": "140px",
        "avg_volume": "140px",
        "best_gain": "120px",
        "worst_loss": "120px",
    })
)

# Apply heatmaps for the key metrics
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")
gt = heatmap(gt, "avg_volume", kind="sequential", hue="neutral")

# Heading band
gt = band(gt)

# Small color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = hairlines(gt)

# Titles and annotations
gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="Monthly trading metrics for 2010–2015"
    )
    .tab_source_note(source_note="Highest single-day gain and loss represent the maximum intraday gain (high − open) and loss (open − low) within each month.")
    .tab_source_note(source_note="Source: S&P 500 historical daily price data (sp500.csv).")
)

# Layout padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

finalize(gt, "table.png")
