import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Read the data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Sort by date
df = df.sort_values("date")

# Calculate intra-month high-low (daily gain/loss)
df["daily_gain"] = df["high"] - df["open"]
df["daily_loss"] = df["open"] - df["low"]

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

# Aggregate monthly data
monthly = df.groupby("year_month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    volume_avg=("volume", "mean"),
    highest_gain=("daily_gain", "max"),
    highest_loss=("daily_loss", "max"),
).reset_index()

# Calculate percent change
monthly["pct_change"] = (
    (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]
)

# Format the year_month for display
monthly["period"] = monthly["year_month"].astype(str)

# Select and reorder columns
monthly = monthly[
    ["period", "open_price", "close_price", "pct_change", "volume_avg", "highest_gain", "highest_loss"]
]

# Create the table
gt = (
    GT(monthly, rowname_col="period")
    .cols_label(
        open_price="Opening Price",
        close_price="Closing Price",
        pct_change="% Change",
        volume_avg="Avg Daily Volume",
        highest_gain="Highest Single-Day Gain",
        highest_loss="Highest Single-Day Loss",
    )
    .fmt_number(
        columns=["open_price", "close_price"],
        decimals=2,
        use_seps=True,
    )
    .fmt_number(
        columns=["volume_avg"],
        decimals=0,
        use_seps=True,
    )
    .fmt_number(
        columns=["highest_gain", "highest_loss"],
        decimals=2,
        use_seps=True,
    )
    .fmt_percent(
        columns=["pct_change"],
        decimals=2,
        force_sign=True,
    )
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[
            float(np.nanmin(monthly[["pct_change"]].to_numpy())),
            float(np.nanmax(monthly[["pct_change"]].to_numpy())),
        ],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["volume_avg"],
        palette="Blues",
        domain=[
            float(np.nanmin(monthly[["volume_avg"]].to_numpy())),
            float(np.nanmax(monthly[["volume_avg"]].to_numpy())),
        ],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening/closing prices, percent change, trading volume, and daily gains/losses",
    )
    .tab_stubhead(label="Period")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_source_note(
        source_note="Percent change is calculated as (close - open) / open. Highest single-day gain/loss represents the largest intraday price movement (high - open and open - low, respectively)."
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily historical data (sp500.csv)."
    )
)

# Render
gt.gtsave("table.png", expand=15)
