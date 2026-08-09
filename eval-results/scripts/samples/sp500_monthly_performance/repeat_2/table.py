import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint

# Load data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Calculate daily gain and loss
df["daily_gain"] = df["high"] - df["open"]
df["daily_loss"] = df["open"] - df["low"]

# Extract year-month for grouping
df["year_month"] = df["date"].dt.to_period("M")

# Monthly aggregation
monthly = (
    df.groupby("year_month")
    .agg(
        open_price=("open", "first"),
        close_price=("close", "last"),
        avg_volume=("volume", "mean"),
        max_daily_gain=("daily_gain", "max"),
        max_daily_loss=("daily_loss", "max"),
    )
    .reset_index()
)

# Calculate percent change
monthly["percent_change"] = (
    (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"] * 100
)

# Filter for 2010-2015
monthly["year"] = monthly["year_month"].dt.year
monthly = monthly[(monthly["year"] >= 2010) & (monthly["year"] <= 2015)].copy()
monthly = monthly.sort_values("year_month").reset_index(drop=True)

# Format year_month as string for display
monthly["month_label"] = monthly["year_month"].astype(str)

# Select and reorder columns
display_df = monthly[
    [
        "month_label",
        "open_price",
        "close_price",
        "percent_change",
        "avg_volume",
        "max_daily_gain",
        "max_daily_loss",
    ]
].copy()

# Rename for display
display_df.columns = [
    "Month",
    "Opening Price",
    "Closing Price",
    "% Change",
    "Avg Daily Volume",
    "Highest Daily Gain",
    "Highest Daily Loss",
]

# Create the table
gt = (
    GT(display_df, rowname_col="Month")
    .fmt_currency(
        columns=["Opening Price", "Closing Price", "Highest Daily Gain", "Highest Daily Loss"],
        currency="USD",
        decimals=2,
    )
    .fmt_percent(columns=["% Change"], decimals=1, scale_values=False)
    .fmt_integer(columns=["Avg Daily Volume"], use_seps=True)
    .data_color(
        columns=["% Change"],
        palette="RdYlGn",
        domain=[-5, 5],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening and closing prices, monthly percent change, average daily volume, and daily extremes",
    )
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
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
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_source_note(
        "Data: S&P 500 historical daily prices. Daily gain = high − open; daily loss = open − low."
    )
)

gt.gtsave("table.png", expand=15)
