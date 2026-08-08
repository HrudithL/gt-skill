import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import frame, finalize, heatmap, PALETTE

# Load data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date").reset_index(drop=True)

# Calculate daily gains/losses for each day
df["daily_return_pct"] = ((df["close"] - df["open"]) / df["open"] * 100)

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date")

    open_price = group.iloc[0]["open"]
    close_price = group.iloc[-1]["close"]
    pct_change = (close_price - open_price) / open_price * 100
    avg_volume = group["volume"].mean()

    # Highest single-day gain and loss
    daily_returns = ((group["close"] - group["open"]) / group["open"] * 100)
    max_daily_gain = daily_returns.max()
    max_daily_loss = daily_returns.min()

    monthly_data.append({
        "Month": str(period),
        "Opening": open_price,
        "Closing": close_price,
        "Monthly % Change": pct_change,
        "Avg Daily Volume": avg_volume,
        "Highest Daily Gain %": max_daily_gain,
        "Highest Daily Loss %": max_daily_loss,
    })

result_df = pd.DataFrame(monthly_data)

# Create GT table
gt = GT(result_df)

# Format numeric columns
gt = gt.fmt_number(
    columns=["Opening", "Closing"],
    decimals=2
)
gt = gt.fmt_number(
    columns=["Monthly % Change", "Highest Daily Gain %", "Highest Daily Loss %"],
    decimals=2
)
gt = gt.fmt_number(
    columns=["Avg Daily Volume"],
    decimals=0
)

# Style the title and subtitle
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010–2015 Monthly Statistics"
)

# Color the monthly % change (diverging measure: negative=bad, positive=good)
gt = heatmap(gt, "Monthly % Change", kind="diverging", hue="default")

# Add hairlines between rows
gt = gt.tab_options(table_body_hlines_style="solid")

# Add source note
gt = gt.tab_source_note(
    source_note=md("**Source:** S&P 500 daily price and volume data (2010–2015). "
                   "Highest daily gain/loss represents the maximum single-day percentage change "
                   "within each month, calculated as (close − open) / open × 100%.")
)

# Apply frame and finalize
gt = frame(gt)
gt = finalize(gt, path="table.png", zoom=2.0, expand=15)
