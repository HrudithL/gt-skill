import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Read the data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Aggregate by year-month
df["year_month"] = df["date"].dt.to_period("M")

monthly = []
for period, group in df.groupby("year_month"):
    # Get first and last row of the month
    first_row = group.iloc[0]
    last_row = group.iloc[-1]

    # Calculate metrics
    open_price = first_row["open"]
    close_price = last_row["close"]
    percent_change = (close_price - open_price) / open_price

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Highest single-day gain (high - low within the day, max across month)
    daily_range = group["high"] - group["low"]
    highest_gain = daily_range.max()

    # Highest single-day loss (as negative value, or track separately)
    # For clarity, we'll show the largest intra-day drop
    highest_loss = -daily_range.max()  # negative for loss

    monthly.append({
        "Period": period.strftime("%b %Y"),
        "Year": period.year,
        "Month": period.month,
        "Open": open_price,
        "Close": close_price,
        "Percent Change": percent_change,
        "Avg Daily Volume": avg_volume,
        "Highest Gain": highest_gain,
        "Highest Loss": highest_loss,
    })

monthly_df = pd.DataFrame(monthly)
monthly_df = monthly_df.sort_values(["Year", "Month"]).reset_index(drop=True)

# Compute symmetric domain for percent change
cols = ["Percent Change"]
lo = float(np.nanmin(monthly_df[cols].to_numpy()))
hi = float(np.nanmax(monthly_df[cols].to_numpy()))
M = max(abs(lo), abs(hi))

# Build the table
gt = (
    GT(monthly_df, rowname_col="Period")
    .cols_hide(columns=["Year", "Month"])
    .fmt_currency(columns=["Open", "Close"], currency="USD", decimals=2)
    .fmt_percent(columns=["Percent Change"], decimals=2, force_sign=True)
    .fmt_number(columns=["Avg Daily Volume"], decimals=0)
    .fmt_currency(columns=["Highest Gain", "Highest Loss"], currency="USD", decimals=2)
    .data_color(
        columns=["Percent Change"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
    )
    .tab_options(
        column_labels_background_color="#F0F0F0",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015 Summary Statistics",
    )
    .opt_row_striping()
    .tab_options(table_width="100%")
)

gt.gtsave("table.png")
