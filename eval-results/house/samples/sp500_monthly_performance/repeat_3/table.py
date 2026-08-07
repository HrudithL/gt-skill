import pandas as pd
from datetime import datetime
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Load the data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Calculate daily gain/loss (high - low and close - open)
df["daily_gain_loss"] = df["high"] - df["low"]
df["daily_pct_change"] = ((df["close"] - df["open"]) / df["open"]) * 100

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

# Calculate monthly statistics
monthly_stats = []

for period in sorted(df["year_month"].unique()):
    month_data = df[df["year_month"] == period].sort_values("date")

    if len(month_data) == 0:
        continue

    # Get first trading day's open and last trading day's close
    opening_price = month_data.iloc[0]["open"]
    closing_price = month_data.iloc[-1]["close"]

    # Calculate percent change for the month
    monthly_pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume
    avg_daily_volume = month_data["volume"].mean()

    # Highest single-day gain (high - low) and loss within month
    day_gains = month_data["high"] - month_data["low"]
    highest_day_gain = day_gains.max()

    # Highest single-day loss (calculated as negative change)
    daily_changes = month_data["close"] - month_data["open"]
    highest_day_loss = daily_changes.min()

    monthly_stats.append({
        "Month": period.strftime("%Y-%m"),
        "Month_Key": str(period),
        "Opening Price": opening_price,
        "Closing Price": closing_price,
        "Percent Change": monthly_pct_change,
        "Avg Daily Volume": avg_daily_volume,
        "Highest Daily Gain": highest_day_gain,
        "Highest Daily Loss": highest_day_loss,
    })

stats_df = pd.DataFrame(monthly_stats).sort_values("Month_Key")
stats_df = stats_df.drop("Month_Key", axis=1)

# Build the table
gt = (
    GT(stats_df)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("2010 through 2015 — opening price, closing price, monthly return, and daily volatility"),
    )
    .fmt_number(columns="Opening Price", decimals=2, use_seps=False)
    .fmt_number(columns="Closing Price", decimals=2, use_seps=False)
    .fmt_number(columns="Percent Change", decimals=2)
    .fmt_number(columns="Avg Daily Volume", decimals=0, use_seps=True)
    .fmt_number(columns="Highest Daily Gain", decimals=2, use_seps=False)
    .fmt_number(columns="Highest Daily Loss", decimals=2, use_seps=False)
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: S&P 500 historical price and volume data (2010-2015).")
)

# Apply humanize_labels to convert column names
gt = humanize_labels(
    gt,
    stats_df,
    overrides={
        "Opening Price": "Opening Price",
        "Closing Price": "Closing Price",
        "Percent Change": "% Change",
        "Avg Daily Volume": "Avg Daily Volume",
        "Highest Daily Gain": "Highest Daily Gain",
        "Highest Daily Loss": "Highest Daily Loss",
    },
)

# Apply heatmap to percent change (diverging, since it can be positive or negative)
gt = heatmap(gt, "Percent Change", kind="diverging", hue="default")

# Apply heading band with forest hue (green for growth/finance theme)
gt = band(gt, hue="forest")

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
