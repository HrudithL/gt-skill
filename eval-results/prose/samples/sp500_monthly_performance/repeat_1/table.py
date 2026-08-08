import numpy as np
import pandas as pd
from great_tables import GT, style, loc

# Read and clean data
df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Add month period and daily change columns
df["month"] = df["date"].dt.to_period("M")
df["daily_change"] = df["close"].pct_change()

# Get the prior year's closing price (end of 2009)
prior_year_close = df.loc[df["date"] == "2009-12-31", "close"]
if len(prior_year_close) == 0:
    # If no 2009 data, use the first value in our dataset
    prior_baseline = df["close"].iloc[0]
else:
    prior_baseline = prior_year_close.iloc[0]

# Aggregate by month
monthly = df.groupby("month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    avg_volume=("volume", "mean"),
).reset_index()

# Calculate percent change month-over-month
monthly["pct_change"] = monthly["close_price"].pct_change()
monthly.loc[monthly.index[0], "pct_change"] = (
    monthly["close_price"].iloc[0] / prior_baseline - 1
)

# Get highest single-day gain and loss within each month
# Compute daily changes across the full series (continuous, not reset per month)
gain_loss = df.groupby("month").agg(
    highest_daily_gain=("daily_change", lambda x: x.max()),
    largest_daily_loss=("daily_change", lambda x: x.min()),
).reset_index()

# Merge gain/loss into monthly summary
monthly = monthly.merge(gain_loss, on="month")

# Format month label as "Mon YYYY"
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

# Reorganize columns
monthly = monthly[[
    "month_label",
    "open_price",
    "close_price",
    "pct_change",
    "avg_volume",
    "highest_daily_gain",
    "largest_daily_loss",
]].reset_index(drop=True)

# Compute symmetric domain for signed measure (percent change)
cols_signed = ["pct_change"]
lo = float(np.nanmin(monthly[cols_signed].to_numpy()))
hi = float(np.nanmax(monthly[cols_signed].to_numpy()))
M = max(abs(lo), abs(hi))

# Build table
gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 — Monthly Performance Summary",
        subtitle="2010–2015 monthly open, close, percent change, volume, and daily extremes",
    )
    .tab_spanner(label="Price", columns=["open_price", "close_price"])
    .tab_spanner(label="Daily Extremes", columns=["highest_daily_gain", "largest_daily_loss"])
    .cols_label(
        month_label="Month",
        open_price="Open",
        close_price="Close",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        highest_daily_gain="Highest Gain",
        largest_daily_loss="Largest Loss",
    )
    # Format prices as currency
    .fmt_currency(columns=["open_price", "close_price"], currency="USD", decimals=2)
    # Format percent change with sign
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    # Format volume as whole number
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    # Format daily extremes as percent with sign
    .fmt_percent(columns=["highest_daily_gain", "largest_daily_loss"], decimals=2, force_sign=True)
    # Diverging color on percent change: RdYlGn, positive=good (default, no reverse)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-M, M],
        na_color="#808080",
        truncate=False,
    )
    # Align columns appropriately
    .cols_align(align="right", columns=["open_price", "close_price", "pct_change", "avg_volume", "highest_daily_gain", "largest_daily_loss"])
    # Add row striping (≥10 rows, not fully covered by Big Color)
    .opt_row_striping()
    # Stub tint (light grey)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Cell borders: hairline between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Frame
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
    # Column-group vertical dividers
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="close_price"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="close_price"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="largest_daily_loss"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="largest_daily_loss"),
    )
    # Source notes: methodology first, then citation
    .tab_source_note(
        source_note="Single-day gains/losses use a continuous day-over-day change across the full 2010–2015 series, not reset at each month's start."
    )
    .tab_source_note(source_note="Source: S&P 500 daily closing prices, 2010–2015.")
)

gt.gtsave("table.png", expand=15)
