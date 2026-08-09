import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Read the S&P 500 data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date")

# Calculate monthly summaries
monthly = []
for year_month, group in df.groupby([df["date"].dt.year, df["date"].dt.month]):
    year, month = year_month
    month_data = group.sort_values("date")

    # Get first and last days
    opening_price = month_data.iloc[0]["open"]
    closing_price = month_data.iloc[-1]["close"]

    # Calculate percent change
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume (in millions)
    avg_volume = month_data["volume"].mean() / 1_000_000

    # Highest single-day gain (max of daily change)
    month_data_copy = month_data.copy()
    month_data_copy["daily_change"] = month_data_copy["close"] - month_data_copy["open"]
    max_gain = month_data_copy["daily_change"].max()

    # Highest single-day loss (min of daily change)
    max_loss = month_data_copy["daily_change"].min()

    # Create a date label (year-month)
    date_label = f"{year}-{month:02d}"

    monthly.append({
        "period": date_label,
        "open": opening_price,
        "close": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "max_gain": max_gain,
        "max_loss": max_loss,
    })

monthly_df = pd.DataFrame(monthly)

# Create the GT table
gt = (
    GT(monthly_df, rowname_col="period")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Opening/closing prices, percent change, volume, and daily extremes — 2010 through 2015"),
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="open", decimals=2)
    .fmt_number(columns="close", decimals=2)
    .fmt_number(columns="pct_change", decimals=2)
    .fmt_number(columns="avg_volume", decimals=1)
    .fmt_number(columns="max_gain", decimals=2)
    .fmt_number(columns="max_loss", decimals=2)
)

gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        "open": "Opening Price",
        "close": "Closing Price",
        "pct_change": "Percent Change (%)",
        "avg_volume": "Avg Daily Volume (M)",
        "max_gain": "Max Daily Gain",
        "max_loss": "Max Daily Loss",
    },
)

# Apply heatmap to percent change (signed/diverging measure)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Band and stub styling
gt = band(gt, hue="forest")
gt = gt.tab_style(
    style=style.fill(color=PALETTE["washed"]["forest"]),
    locations=loc.stub(),
)

gt = gt.tab_source_note(source_note="Source: provided dataset (daily S&P 500 data).")
gt = frame(gt)

finalize(gt, path="table.png")
