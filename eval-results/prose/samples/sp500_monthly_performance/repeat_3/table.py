"""S&P 500 Monthly Performance Summary, 2010-2015."""
import numpy as np
import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Create month-year period
df["month"] = df["date"].dt.to_period("M")

# Compute daily returns across the full series (continuous, not reset at month boundaries)
df["daily_return"] = df["close"].pct_change()

# Aggregate by month
monthly = df.groupby("month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    high_price=("high", "max"),
    low_price=("low", "min"),
    volume_avg=("volume", "mean"),
    daily_return_max=("daily_return", "max"),
    daily_return_min=("daily_return", "min"),
)

# Month-to-month price change
monthly["pct_change"] = monthly["close_price"].pct_change()

# For the first month of 2010, get the prior close to anchor the return
first_month = monthly.index[0]
prior_year_close = df.loc[df["date"] == "2009-12-31", "close"]
if not prior_year_close.empty:
    prior_close = prior_year_close.iloc[0]
    monthly.loc[first_month, "pct_change"] = (
        monthly.loc[first_month, "close_price"] / prior_close - 1
    )

# Reset and label
monthly = monthly.reset_index()
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

# Reorder columns
monthly = monthly[[
    "month_label",
    "open_price",
    "close_price",
    "pct_change",
    "volume_avg",
    "daily_return_max",
    "daily_return_min",
]].reset_index(drop=True)

# Compute symmetric domain for the single signed measure (pct_change)
pc_m = float(np.nanmax(np.abs(monthly["pct_change"].to_numpy())))
dr_m = float(np.nanmax(np.abs(monthly[["daily_return_max", "daily_return_min"]].to_numpy())))

gt = (
    GT(monthly)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening, closing, returns, volume, and intraday extremes",
    )
    .cols_label(
        month_label="Month",
        open_price="Open ($)",
        close_price="Close ($)",
        pct_change="MoM Change",
        volume_avg="Avg Daily Volume",
        daily_return_max="Highest Daily Gain",
        daily_return_min="Lowest Daily Loss",
    )
    # Format prices as currency
    .fmt_currency(
        columns=["open_price", "close_price"],
        currency="USD",
        decimals=2,
    )
    # Format percentages with sign
    .fmt_percent(
        columns=["pct_change"],
        decimals=2,
        force_sign=True,
    )
    .fmt_percent(
        columns=["daily_return_max", "daily_return_min"],
        decimals=2,
        force_sign=True,
    )
    # Format volume with thousands separators
    .fmt_number(
        columns=["volume_avg"],
        decimals=0,
        use_seps=True,
    )
    # Color the month-over-month change with diverging RdYlGn
    # Use a single domain across all signed measures for consistency
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pc_m, pc_m],
        na_color="#808080",
        truncate=False,
    )
    # Alignment
    .cols_align(align="left", columns=["month_label"])
    .cols_align(align="right", columns=[
        "open_price", "close_price", "pct_change",
        "volume_avg", "daily_return_max", "daily_return_min"
    ])
    # Small-Color polish per checklist
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
    # Row striping (≥10 rows, ≥5 rows for caption)
    .opt_row_striping()
    # Caption and source note (separate calls, methodology first)
    .tab_source_note(
        source_note="Single-day gains/losses use continuous day-over-day change "
                     "across the full historical series, not reset at each month's start."
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily closing prices, 2010–2015."
    )
)

gt.gtsave("table.png", expand=15)
