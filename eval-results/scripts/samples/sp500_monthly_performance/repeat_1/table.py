import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, heatmap, PALETTE

# Step 1: Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])
df_raw = df_raw.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]

# Compute daily gain/loss (day-over-day continuous change across full series)
df_raw["daily_change"] = df_raw["close"].pct_change()
df_raw["daily_gain_loss"] = df_raw["close"].diff()

# Group by month
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Aggregate by month
monthly = df_raw.groupby("year_month").agg({
    "open": "first",           # opening price of first trading day
    "close": "last",           # closing price of last trading day
    "volume": "mean",          # average daily volume
    "daily_gain_loss": lambda x: x.max(),  # highest single-day gain (max of daily changes)
}).reset_index()

# Add highest single-day loss (min of daily changes, shown as positive number)
monthly["highest_daily_loss"] = df_raw.groupby("year_month")["daily_gain_loss"].apply(lambda x: -x.min()).values

# Compute percent change
monthly["pct_change"] = ((monthly["close"] - monthly["open"]) / monthly["open"] * 100)

# Rename columns for display
monthly = monthly.rename(columns={
    "year_month": "Month",
    "open": "Opening Price",
    "close": "Closing Price",
    "pct_change": "Monthly % Change",
    "volume": "Avg Daily Volume",
    "daily_gain_loss": "Highest Daily Gain",
    "highest_daily_loss": "Highest Daily Loss",
})

# Step 2: Organize columns
# Stub: Month
# Stub format to "Mon YYYY"
monthly["Month"] = monthly["Month"].astype(str).apply(
    lambda x: pd.to_datetime(x).strftime("%b %Y")
)

# Reorder columns
monthly = monthly[[
    "Month",
    "Opening Price",
    "Closing Price",
    "Monthly % Change",
    "Avg Daily Volume",
    "Highest Daily Gain",
    "Highest Daily Loss",
]]

# Step 3: Big Color decision
# We have percent change (signed, can be negative), highest daily gain (positive magnitude),
# highest daily loss (positive magnitude). The prompt emphasizes percent change first.
# Qualifying measures: Monthly % Change (signed), Highest Daily Gain (magnitude), Highest Daily Loss (magnitude)
# Per priority: Monthly % Change is explicitly mentioned first → ranks first
# Between Highest Daily Gain and Loss, Gain appears first in the request → ranks second
# So we color: Monthly % Change (diverging) and Highest Daily Gain (sequential)

# Step 4: Determine heading band
# We have Big Color, so use LIGHT band with washed tint
# Primary measure is percent change (signed) → RdYlGn diverging → use washed-DA Navy tint

# Step 5: Small Color polish

# Step 6: Titles and annotations

# Compute diverging domain for % change (symmetric around 0)
pct_max = abs(monthly["Monthly % Change"]).max()
pct_domain = [-pct_max, pct_max]

# Compute sequential domain for highest daily gain
gain_lo = float(np.nanmin(monthly[["Highest Daily Gain"]].to_numpy()))
gain_hi = float(np.nanmax(monthly[["Highest Daily Gain"]].to_numpy()))

# Step 7: Build the table
gt = (
    GT(monthly, rowname_col="Month")
    # Format columns
    .fmt_number(columns=["Opening Price", "Closing Price"], decimals=2, use_seps=True)
    .fmt_number(columns=["Monthly % Change"], decimals=2)
    .fmt_number(columns=["Avg Daily Volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["Highest Daily Gain", "Highest Daily Loss"], decimals=2, use_seps=True)
    # Small Color: cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Small Color: stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),  # washed Navy tint
        locations=loc.stub(),
    )
    # Small Color: row striping (72 rows, triggers)
    .opt_row_striping()
    # Big Color: Monthly % Change diverging fill
    .data_color(
        columns=["Monthly % Change"],
        palette="RdYlGn",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # Big Color: Highest Daily Gain sequential fill
    .data_color(
        columns=["Highest Daily Gain"],
        palette="Blues",
        domain=[gain_lo, gain_hi],
        truncate=False,
        na_color="#808080",
    )
    # Heading band - light with washed Navy tint
    .tab_options(
        column_labels_background_color="#EAF0F6",
    )
    # Titles
    .tab_header(
        title="S&P 500 Monthly Performance (2010–2015)",
        subtitle="Opening/closing prices, monthly percentage change, average daily volume, and highest single-day gains and losses per month"
    )
    # Source note with methodology
    .tab_source_note(
        source_note="Single-day gains and losses use continuous day-over-day changes across the full historical series, not reset at each month's start."
    )
    .tab_source_note(
        source_note="Source: S&P 500 historical price dataset."
    )
)

# Apply frame and finalize
gt = frame(gt)
finalize(gt)
