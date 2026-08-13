"""S&P 500 Monthly Performance Summary Table (2010-2015)"""

import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load and prepare data
df = pd.read_csv("sp500.csv", parse_dates=["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df = df.sort_values("date").reset_index(drop=True)

# Add year-month column for grouping
df["year_month"] = df["date"].dt.to_period("M")

# Group by month and calculate summary metrics
monthly_data = []
for period, group in df.groupby("year_month"):
    year = period.year
    month = period.month

    # Opening price (first trading day of month)
    open_price = group.iloc[0]["open"]

    # Closing price (last trading day of month)
    close_price = group.iloc[-1]["close"]

    # Percent change for the month
    pct_change = ((close_price - open_price) / open_price) * 100

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Daily gains and losses
    group["daily_change"] = group["close"] - group["open"]
    highest_gain = group["daily_change"].max()
    largest_loss = group["daily_change"].min()

    monthly_data.append({
        "year": year,
        "month": month,
        "year_month": period,
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "highest_gain": highest_gain,
        "largest_loss": largest_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Create month labels
month_names = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
monthly_df["month_label"] = monthly_df["month"].map(month_names)
monthly_df["period"] = monthly_df["year"].astype(str) + "-" + monthly_df["month_label"]

# Create the GT table
gt = GT(data=monthly_df, rowname_col="period", groupname_col="year")

# Apply column labels
gt = humanize_labels(gt, monthly_df, overrides={
    "period": "Period",
    "year": "Year",
    "month": "Month",
    "year_month": "Year-Month",
    "open": "Open",
    "close": "Close",
    "pct_change": "Pct Change",
    "avg_volume": "Avg Daily Volume",
    "highest_gain": "Highest Daily Gain",
    "largest_loss": "Largest Daily Loss",
    "month_label": "Month Label",
})

# Format currency columns
gt = gt.fmt_currency(
    columns=["open", "close", "highest_gain", "largest_loss"],
    currency="USD",
    decimals=2,
)

# Format percent change
gt = gt.fmt_percent(
    columns=["pct_change"],
    decimals=1,
    scale_values=False,
    force_sign=True,
)

# Format volume
gt = gt.fmt_integer(columns=["avg_volume"])

# Hide helper columns
gt = gt.cols_hide(columns=["year", "month", "year_month", "month_label"])

# Apply heatmap to percent change (diverging - the hero measure)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Add branding
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)
gt = frame(gt)
gt = hairlines(gt)

# Add header and notes
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010 through 2015"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Percent change is calculated from monthly open to close prices, with positive returns shown in green and negative in red."
)
gt = gt.tab_source_note(
    source_note="Source: provided S&P 500 historical daily data (sp500.csv)."
)

# Add styling to group headers
gt = gt.tab_style(
    style=style.text(weight="bold"),
    locations=loc.row_groups()
)

# Render
finalize(gt, path="table.png")
