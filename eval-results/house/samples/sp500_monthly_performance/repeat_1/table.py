import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].sort_values("date")

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

monthly = []
for period, group in df.groupby("year_month"):
    year, month = period.year, period.month

    # Opening price (first trading day of month)
    opening = group.iloc[0]["open"]

    # Closing price (last trading day of month)
    closing = group.iloc[-1]["close"]

    # Percent change
    pct_change = ((closing - opening) / opening) * 100

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Highest single-day gain (close - open)
    group["daily_gain"] = group["close"] - group["open"]
    highest_gain = group["daily_gain"].max()

    # Highest single-day loss (most negative close - open)
    highest_loss = group["daily_gain"].min()

    monthly.append({
        "Period": f"{year}-{month:02d}",
        "Year": year,
        "Month": month,
        "Opening": opening,
        "Closing": closing,
        "Pct Change": pct_change,
        "Avg Volume": avg_volume,
        "Highest Gain": highest_gain,
        "Highest Loss": highest_loss,
    })

result_df = pd.DataFrame(monthly)

# Create display dataframe without Year/Month columns
display_df = result_df[["Period", "Opening", "Closing", "Pct Change", "Avg Volume", "Highest Gain", "Highest Loss"]].copy()

gt = (
    GT(display_df, rowname_col="Period")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("2010–2015: Monthly opening/closing prices, returns, volume, and daily extremes"),
    )
    .fmt_currency(columns=["Opening", "Closing", "Highest Gain", "Highest Loss"], decimals=2)
    .fmt_percent(columns="Pct Change", decimals=2, scale_values=False)
    .fmt_number(columns="Avg Volume", decimals=0, use_seps=True)
    .tab_source_note(source_note="Source: provided dataset.")
)

# Apply color to percent change (diverging: red for losses, green for gains)
gt = heatmap(gt, "Pct Change", kind="diverging", hue="default")

# Apply band and other styling
gt = band(gt, hue="navy")
gt = hairlines(gt)
gt = frame(gt)

finalize(gt, path="table.png")
