import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Read the data
df_daily = pd.read_csv("sp500.csv")
df_daily["date"] = pd.to_datetime(df_daily["date"])

# Filter for 2010-2015
df_daily = df_daily[(df_daily["date"] >= "2010-01-01") & (df_daily["date"] <= "2015-12-31")]

# Sort by date ascending
df_daily = df_daily.sort_values("date").reset_index(drop=True)

# Extract year-month
df_daily["year_month"] = df_daily["date"].dt.to_period("M")

# Group by month and compute aggregations
monthly = []
for period, group in df_daily.groupby("year_month"):
    year = period.year
    month = period.month

    # Opening price (first trading day of the month)
    open_price = group.iloc[0]["open"]

    # Closing price (last trading day of the month)
    close_price = group.iloc[-1]["close"]

    # Percent change
    pct_change = (close_price - open_price) / open_price

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Highest single-day gain (max of high - low for each day, or max of high - open/prev close)
    # Using: highest single-day gain = max(close - open) for each day
    daily_gains = group["close"] - group["open"]
    highest_gain = daily_gains.max()

    # Highest single-day loss = min(close - open) for each day
    daily_losses = group["close"] - group["open"]
    highest_loss = daily_losses.min()

    monthly.append({
        "year_month": f"{period}",
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day_gain": highest_gain,
        "worst_day_loss": highest_loss,
    })

df = pd.DataFrame(monthly)

# Ensure numeric columns are floats
for col in ["open", "close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Create the GT table
gt = (
    GT(df, rowname_col="year_month")
    # Format columns
    .fmt_currency(columns=["open", "close"], decimals=2, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=1, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_currency(columns=["best_day_gain", "worst_day_loss"], decimals=2)
    # Rename columns for display
    .cols_label(
        open="Opening Price",
        close="Closing Price",
        pct_change="Monthly % Change",
        avg_volume="Avg Daily Volume",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss"
    )
    # Column widths
    .cols_width(cases={
        "year_month": "140px",
        "open": "130px",
        "close": "130px",
        "pct_change": "140px",
        "avg_volume": "160px",
        "best_day_gain": "140px",
        "worst_day_loss": "140px"
    })
    # Add diverging color to percent change (signed measure)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[
            -max(abs(df["pct_change"].min()), abs(df["pct_change"].max())),
            max(abs(df["pct_change"].min()), abs(df["pct_change"].max()))
        ],
        truncate=False
    )
    # Heading band
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Frame borders
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
    # Body row hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    # Padding
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening/closing prices, monthly percent change, trading volume, and daily extremes"
    )
    # Footer notes
    .tab_source_note(
        source_note="Best day gain and worst day loss represent the maximum single-day close-to-close change within each month."
    )
    .tab_source_note(
        source_note="Source: S&P 500 historical daily data"
    )
)

gt.gtsave("table.png", expand=15)
