import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, finalize, stripe, stub_tint, heatmap

# Load data and prepare
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Compute daily percentage change
df["daily_pct_change"] = df["close"].pct_change()

# Extract year-month for grouping
df["year_month"] = df["date"].dt.to_period("M")

# Monthly aggregations
monthly_data = []
for year_month in sorted(df["year_month"].unique()):
    month_df = df[df["year_month"] == year_month]

    opening_price = month_df.iloc[0]["open"]
    closing_price = month_df.iloc[-1]["close"]
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = month_df["volume"].mean()

    # Highest single-day gain and loss (from daily_pct_change computed continuously)
    highest_gain = month_df["daily_pct_change"].max()
    lowest_loss = month_df["daily_pct_change"].min()

    monthly_data.append({
        "month": str(year_month),
        "opening_price": opening_price,
        "closing_price": closing_price,
        "percent_change": percent_change,
        "avg_daily_volume": avg_daily_volume,
        "highest_gain": highest_gain if pd.notna(highest_gain) else None,
        "lowest_loss": lowest_loss if pd.notna(lowest_loss) else None,
    })

monthly_df = pd.DataFrame(monthly_data)

# Parse month string and format as "Mon YYYY"
monthly_df["month_parsed"] = pd.to_datetime(monthly_df["month"].astype(str))
monthly_df["month_formatted"] = monthly_df["month_parsed"].dt.strftime("%b %Y")
monthly_df = monthly_df[["month_formatted", "opening_price", "closing_price", "percent_change",
                         "avg_daily_volume", "highest_gain", "lowest_loss"]].copy()
monthly_df.columns = ["month", "opening_price", "closing_price", "percent_change",
                      "avg_daily_volume", "highest_gain", "lowest_loss"]

# Create table
gt = (
    GT(monthly_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Opening/closing prices, percent change, average daily volume, and daily gains/losses by month, 2010–2015"),
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="opening_price", decimals=2)
    .fmt_number(columns="closing_price", decimals=2)
    .fmt_percent(columns="percent_change", decimals=2, scale_values=False)
    .fmt_number(columns="avg_daily_volume", decimals=0, use_seps=True)
    .fmt_percent(columns="highest_gain", decimals=2, scale_values=False)
    .fmt_percent(columns="lowest_loss", decimals=2, scale_values=False)
    .sub_missing(columns=["highest_gain", "lowest_loss"], missing_text="—")
)

# Apply humanize labels via direct cols_label call
gt = gt.cols_label(
    opening_price="Opening Price",
    closing_price="Closing Price",
    percent_change="Monthly %",
    avg_daily_volume="Avg Daily Volume",
    highest_gain="Highest Daily Gain",
    lowest_loss="Lowest Daily Loss",
)

# Heatmap the percent_change (signed value -> diverging)
# Compute symmetric domain for percent change
pct_m = max(abs(monthly_df["percent_change"].min()), abs(monthly_df["percent_change"].max()))
gt = heatmap(gt, "percent_change", kind="diverging", hue="default", domain=[-pct_m, pct_m])

# Column label band (light tint, navy)
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Row striping and stub tint
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Frame and finalize
gt = frame(gt)

# Source notes: methodology first, then citation
gt = (
    gt.tab_source_note(
        source_note="Single-day gain/loss use a continuous day-over-day change across the full historical series, not reset at each month's start.",
    )
    .tab_source_note(source_note="Source: provided S&P 500 dataset.")
)

finalize(gt, path="table.png", zoom=2.0, expand=15)
