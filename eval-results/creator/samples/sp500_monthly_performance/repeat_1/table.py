import sys
sys.path.insert(0, '/Users/hrudithl/Documents/posit-dev/gtskill/.claude/skills/great-tables')

import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

# Read the data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df_filtered = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Create year-month column for grouping
df_filtered["year_month"] = df_filtered["date"].dt.to_period("M")

# Calculate monthly statistics
monthly_stats = []
for period, group in df_filtered.groupby("year_month"):
    group = group.sort_values("date")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = group["volume"].mean()

    # Calculate daily gains/losses
    group["daily_change"] = group["high"] - group["low"]
    highest_gain = group["daily_change"].max()
    highest_loss = -(group["close"] - group["open"]).min()  # Most negative close relative to open

    monthly_stats.append({
        "date": period.strftime("%Y-%m"),
        "year": int(period.year),
        "month": period.month,
        "opening_price": opening_price,
        "closing_price": closing_price,
        "percent_change": percent_change,
        "avg_daily_volume": avg_daily_volume,
        "highest_single_day_gain": highest_gain,
        "highest_single_day_loss": highest_loss,
    })

stats_df = pd.DataFrame(monthly_stats)

# Create the table
tbl = (
    GT(stats_df)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Daily and monthly metrics for 2010–2015"),
    )
    .fmt_number(columns="opening_price", decimals=2)
    .fmt_number(columns="closing_price", decimals=2)
    .fmt_percent(columns="percent_change", decimals=2)
    .fmt_integer(columns="avg_daily_volume")
    .fmt_number(columns="highest_single_day_gain", decimals=2)
    .fmt_number(columns="highest_single_day_loss", decimals=2)
    .cols_hide(columns=["year", "month"])
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Data: S&P 500 daily prices and volumes, 2010–2015.")
)

tbl = humanize_labels(
    tbl,
    stats_df,
    overrides={
        "opening_price": "Opening Price",
        "closing_price": "Closing Price",
        "percent_change": "Monthly % Change",
        "avg_daily_volume": "Avg Daily Volume",
        "highest_single_day_gain": "Highest Daily Gain",
        "highest_single_day_loss": "Highest Daily Loss",
    }
)

tbl = add_heatmap(tbl, stats_df, "percent_change")
tbl = apply_house_style(tbl)

tbl.gtsave("table.png", zoom=2, expand=10)
