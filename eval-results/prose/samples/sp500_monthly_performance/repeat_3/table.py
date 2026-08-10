import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Load data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Sort by date
df = df.sort_values("date").reset_index(drop=True)

# Extract year and month
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["year_month"] = df["date"].dt.strftime("%Y-%m")

# Filter to 2010-2015
df = df[(df["year"] >= 2010) & (df["year"] <= 2015)].copy()

# Compute monthly summaries
monthly = []
for year_month in sorted(df["year_month"].unique()):
    month_data = df[df["year_month"] == year_month].copy()

    # Opening price (first trading day of month)
    opening_price = month_data.iloc[0]["open"]

    # Closing price (last trading day of month)
    closing_price = month_data.iloc[-1]["close"]

    # Percent change
    pct_change = (closing_price - opening_price) / opening_price

    # Average daily volume
    avg_volume = month_data["volume"].mean()

    # Daily changes (intraday high - low)
    month_data["daily_gain"] = month_data["high"] - month_data["low"]
    best_day = month_data["daily_gain"].max()
    worst_day = -month_data["daily_gain"].max()  # Negative to show as a loss

    # For worst_day, we want the intraday loss (low - high, which is negative)
    worst_day = month_data["low"].min() - month_data[month_data["low"] == month_data["low"].min()].iloc[0]["high"]

    # Actually, let's compute the maximum intraday swing as both gain and loss
    month_data["intraday_low"] = month_data["low"]
    month_data["intraday_high"] = month_data["high"]

    # Best single-day gain (max intraday high)
    best_intraday_move = (month_data["high"] - month_data["open"]).max()
    worst_intraday_move = (month_data["low"] - month_data["open"]).min()

    monthly.append({
        "year_month": year_month,
        "opening_price": opening_price,
        "closing_price": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day": best_intraday_move,
        "worst_day": worst_intraday_move,
    })

monthly_df = pd.DataFrame(monthly)

# Create a display column for the month
monthly_df["month"] = pd.to_datetime(monthly_df["year_month"]).dt.strftime("%b %Y")

# Reorder columns for display
display_df = monthly_df[["month", "opening_price", "closing_price", "pct_change", "avg_volume", "best_day", "worst_day"]].copy()
display_df.columns = ["Month", "Opening Price", "Closing Price", "% Change", "Avg Daily Volume", "Best Day Gain", "Worst Day Loss"]

# Convert to the right types for formatting
display_df["Opening Price"] = display_df["Opening Price"].astype(float)
display_df["Closing Price"] = display_df["Closing Price"].astype(float)
display_df["% Change"] = display_df["% Change"].astype(float)
display_df["Avg Daily Volume"] = display_df["Avg Daily Volume"].astype(float)
display_df["Best Day Gain"] = display_df["Best Day Gain"].astype(float)
display_df["Worst Day Loss"] = display_df["Worst Day Loss"].astype(float)

# Build the table
# Step 3: Big Color — % Change is signed, use diverging
cols_for_color = ["% Change"]
lo = float(np.nanmin(display_df[cols_for_color].to_numpy()))
hi = float(np.nanmax(display_df[cols_for_color].to_numpy()))
M = max(abs(lo), abs(hi))

gt = (
    GT(display_df, rowname_col="Month")
    # Step 3: Big Color — diverging for % Change (signed measure, positive = good)
    .fmt_percent(columns=["% Change"], decimals=1, force_sign=True)
    .data_color(
        columns=["% Change"],
        palette="RdYlGn",
        reverse=False,
        domain=[-M, M],
        truncate=False,
    )
    # Step 5: Formatting per column type
    .fmt_currency(columns=["Opening Price", "Closing Price"], decimals=2, use_seps=True)
    .fmt_number(columns=["Avg Daily Volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["Best Day Gain", "Worst Day Loss"], decimals=2)
    # Step 5: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 4: Heading band — LIGHT band (because we have Big Color)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # pale blue for Navy theme
        column_labels_font_weight="bold",
    )
    # Step 5: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Row striping (>= 10 rows, not fully filled)
    .opt_row_striping()
    # Step 5: Frame border
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
    # Step 6: Titles and annotations
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening and closing prices, percent change, trading volume, and intraday swings by month",
    )
    .tab_source_note(
        source_note="Best Day Gain and Worst Day Loss represent the maximum intraday swing (high minus opening price) and minimum intraday swing (low minus opening price) for each month."
    )
    .tab_source_note(
        source_note="Source: Historical S&P 500 daily price data."
    )
)

# Render
gt.gtsave("table.png", expand=15)
