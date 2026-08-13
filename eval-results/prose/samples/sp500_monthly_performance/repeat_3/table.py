import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Understand and clean the data
df_raw = pd.read_csv("sp500.csv", parse_dates=["date"])
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Filter to 2010-2015
df_raw = df_raw[df_raw["date"].dt.year >= 2010]
df_raw = df_raw[df_raw["date"].dt.year <= 2015]

# Calculate daily gains/losses (within-day and prev-close comparisons)
df_raw["daily_gain"] = df_raw["high"] - df_raw["open"]
df_raw["daily_loss"] = df_raw["open"] - df_raw["low"]

# Group by year-month
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Aggregate by month
monthly = df_raw.groupby("year_month").agg(
    month_open=("open", "first"),
    month_close=("close", "last"),
    avg_volume=("volume", "mean"),
    max_daily_gain=("daily_gain", "max"),
    max_daily_loss=("daily_loss", "max"),
).reset_index()

# Calculate percent change (close - open) / open
monthly["pct_change"] = np.where(
    monthly["month_open"] > 0,
    (monthly["month_close"] - monthly["month_open"]) / monthly["month_open"],
    np.nan
)

# Create display-friendly month label
monthly["period"] = monthly["year_month"].astype(str)

# Reorder columns
monthly = monthly[
    ["period", "month_open", "month_close", "pct_change", "avg_volume", "max_daily_gain", "max_daily_loss"]
]

# Step 2: Organize columns - period is the stub
# Period order is already chronological from groupby

# Step 3: Big Color decisions
# pct_change is diverging (signed, good/bad on both sides)
# avg_volume is neutral magnitude sequential
# max_daily_gain is neutral magnitude sequential
# max_daily_loss is neutral magnitude sequential
# All four qualify as distinct dimensions of "monthly performance" per small_color.md redundancy check

# Domains for color
cols_volume = ["avg_volume"]
vol_lo = float(np.nanmin(monthly[cols_volume].to_numpy()))
vol_hi = float(np.nanmax(monthly[cols_volume].to_numpy()))

cols_gain = ["max_daily_gain"]
gain_lo = float(np.nanmin(monthly[cols_gain].to_numpy()))
gain_hi = float(np.nanmax(monthly[cols_gain].to_numpy()))

cols_loss = ["max_daily_loss"]
loss_lo = float(np.nanmin(monthly[cols_loss].to_numpy()))
loss_hi = float(np.nanmax(monthly[cols_loss].to_numpy()))

# Symmetric domain for pct_change (diverging)
cols_pct = ["pct_change"]
pct_lo = float(np.nanmin(monthly[cols_pct].to_numpy()))
pct_hi = float(np.nanmax(monthly[cols_pct].to_numpy()))
M = max(abs(pct_lo), abs(pct_hi))

# Step 4 & 5 & 6: Build the table with all formatting
gt = (
    GT(monthly, rowname_col="period")
    .cols_label(
        month_open="Open",
        month_close="Close",
        pct_change="% Change",
        avg_volume="Avg Volume",
        max_daily_gain="Best Day Gain",
        max_daily_loss="Worst Day Loss",
    )
    # Format numbers
    .fmt_number(
        columns=["month_open", "month_close", "max_daily_gain", "max_daily_loss"],
        decimals=2,
    )
    .fmt_number(
        columns=["avg_volume"],
        decimals=0,
    )
    .fmt_percent(
        columns=["pct_change"],
        decimals=2,
        force_sign=True,
    )
    # Step 3: Big Color - diverging for pct_change
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
        na_color="#808080",
    )
    # Step 3: Big Color - sequential for volume (neutral magnitude -> Blues)
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 3: Big Color - sequential for max_daily_gain (magnitude -> Blues)
    .data_color(
        columns=["max_daily_gain"],
        palette="Blues",
        domain=[gain_lo, gain_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 3: Big Color - sequential for max_daily_loss (magnitude -> Blues)
    .data_color(
        columns=["max_daily_loss"],
        palette="Blues",
        domain=[loss_lo, loss_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed navy)
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015: Opening/Closing Prices, Monthly Returns, and Volatility",
    )
    .tab_stubhead(label="Month")
    # Step 5: Small Color checklist
    # (a) Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_border_left_color="light gray",
        table_border_left_width="1px",
        table_border_right_color="light gray",
        table_border_right_width="1px",
        table_border_top_color="light gray",
        table_border_top_width="1px",
        table_border_bottom_color="light gray",
        table_border_bottom_width="1px",
    )
    # (c) Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
    )
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 6: Titles & annotations - footer notes (two separate calls)
    .tab_source_note(
        "Monthly percent change computed as (closing price − opening price) / opening price. "
        "Best/worst day gain/loss represents the maximum intraday high minus open and open minus intraday low, respectively."
    )
    .tab_source_note(
        "Data source: S&P 500 daily prices, 2010–2015."
    )
)

# Step 7: Render
gt.gtsave("table.png")
print("Table rendered successfully to table.png")
