import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Sort by date for grouping
df = df.sort_values("date").reset_index(drop=True)

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

# Calculate monthly stats
monthly = df.groupby("year_month").agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    high_price=("high", "max"),
    low_price=("low", "min"),
    volume=("volume", "mean"),
).reset_index()

# Calculate percent change and daily gains/losses
monthly["pct_change"] = (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]

# For highest single-day gain and loss within each month
# Calculate daily gain/loss for all rows
df["daily_gain"] = df["high"] - df["open"]
df["daily_loss"] = df["open"] - df["low"]

# Get max gain and max loss per month
extremes = df.groupby("year_month").agg(
    max_daily_gain=("daily_gain", "max"),
    max_daily_loss=("daily_loss", "max"),
).reset_index()

# Merge extremes back
monthly = monthly.merge(extremes, on="year_month")

# Convert period to string for display
monthly["period"] = monthly["year_month"].astype(str)
monthly = monthly[["period", "open_price", "close_price", "pct_change", "volume", "max_daily_gain", "max_daily_loss"]]

# Rename columns for display
monthly = monthly.rename(columns={
    "open_price": "Open",
    "close_price": "Close",
    "pct_change": "% Change",
    "volume": "Avg Volume",
    "max_daily_gain": "Max Daily Gain",
    "max_daily_loss": "Max Daily Loss",
})

# Step 2: Organize columns with stub
gt = GT(
    monthly,
    rowname_col="period"
)

# Step 3: Big Color — diverging fill for signed measure (% Change)
# Symmetric, data-driven domain
cols_color = ["% Change"]
lo = float(np.nanmin(monthly[cols_color].to_numpy()))
hi = float(np.nanmax(monthly[cols_color].to_numpy()))
M = max(abs(lo), abs(hi))

gt = gt.data_color(
    columns=cols_color,
    palette="RdYlGn",
    reverse=False,
    domain=[-M, M],
    truncate=False,
)

# Step 5: Polish — formatters and styling
gt = (
    gt
    # Format columns
    .fmt_currency(columns=["Open", "Close"], decimals=2, currency="USD")
    .fmt_number(columns=["Avg Volume"], decimals=0, use_seps=True)
    .fmt_currency(columns=["Max Daily Gain", "Max Daily Loss"], decimals=2, currency="USD")
    .fmt_percent(columns=["% Change"], decimals=2, force_sign=True)
    # Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Stub tint
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 4: Light heading band (with Big Color present)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
    )
    # Frame border
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
    # Titles
    .tab_header(
        title="S&P 500 Monthly Performance (2010–2015)",
        subtitle="Opening price, closing price, percent change, average daily volume, and highest single-day gain and loss within each month"
    )
    # Source note with methodology
    .tab_source_note("Definition: % Change = (closing − opening) / opening. Max Daily Gain = (high − open). Max Daily Loss = (open − low).")
)

# Render
gt.gtsave("table.png", expand=15)
