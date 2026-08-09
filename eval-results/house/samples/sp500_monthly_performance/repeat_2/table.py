import pandas as pd
from datetime import datetime
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, finalize, heatmap

# Load the S&P 500 data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date")

# Extract year and month
df["year_month"] = df["date"].dt.to_period("M")

# Group by month and calculate summary statistics
monthly_stats = []
for year_month, group in df.groupby("year_month"):
    # Get first and last row for the month
    first_row = group.iloc[0]
    last_row = group.iloc[-1]

    # Calculate metrics
    opening_price = first_row["open"]
    closing_price = last_row["close"]
    percent_change = (closing_price - opening_price) / opening_price  # As decimal for fmt_percent
    avg_daily_volume = group["volume"].mean() / 1_000_000  # Convert to millions

    # Find highest single-day gain and loss
    group["daily_change"] = group["close"] - group["open"]
    highest_gain = group["daily_change"].max()
    highest_loss = group["daily_change"].min()

    monthly_stats.append({
        "Month": str(year_month),
        "Open": opening_price,
        "Close": closing_price,
        "% Change": percent_change,
        "Avg Daily Vol (M)": avg_daily_volume,
        "Highest Gain": highest_gain,
        "Highest Loss": highest_loss,
    })

# Create DataFrame with monthly data
monthly_df = pd.DataFrame(monthly_stats)

# Create GT table
gt = GT(monthly_df)

# Add title and subtitle
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010 – 2015 monthly opening/closing prices, percent change, volume, and daily extremes"
)

# Format columns
gt = gt.fmt_number(
    columns=["Open", "Close"],
    decimals=2
)

gt = gt.fmt_percent(
    columns=["% Change"],
    decimals=2
)

gt = gt.fmt_number(
    columns=["Avg Daily Vol (M)"],
    decimals=1
)

gt = gt.fmt_number(
    columns=["Highest Gain", "Highest Loss"],
    decimals=2
)

# Apply heatmap to percent change column (diverging, centered at 0)
gt = heatmap(
    gt,
    columns=["% Change"],
    kind="diverging",
    hue="default",
)

# Apply heatmap to average daily volume (sequential)
gt = heatmap(
    gt,
    columns=["Avg Daily Vol (M)"],
    kind="sequential",
    hue="neutral",
)

# Add source note
gt = gt.tab_source_note(
    source_note="Source: provided dataset. Daily extremes represent the highest single-day intraday gain and loss within each month."
)

# Add frame
gt = frame(gt)

# Add row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Finalize and save
finalize(gt, path="table.png", zoom=2.0, expand=15)
