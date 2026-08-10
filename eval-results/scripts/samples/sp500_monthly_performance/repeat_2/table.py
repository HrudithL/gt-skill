import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, band, stripe

# Step 1: Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Filter to 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]

# Extract year-month for grouping
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

# Compute monthly aggregations
monthly_data = []
for period, group in df_raw.groupby("year_month"):
    group = group.sort_values("date")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group["volume"].mean()

    # Daily gains and losses
    group["daily_change"] = group["close"] - group["open"]
    highest_gain = group["daily_change"].max()
    highest_loss = group["daily_change"].min()

    monthly_data.append({
        "period": str(period),
        "open": opening_price,
        "close": closing_price,
        "pct_change": percent_change,
        "avg_volume": avg_volume,
        "high_gain": highest_gain,
        "high_loss": highest_loss,
    })

df = pd.DataFrame(monthly_data)

# Step 2: Organize columns with stub
df = df.set_index("period")
df.index.name = None

# Step 3: Color the percent_change (signed measure - diverging)
cols_to_color = ["pct_change"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))
M = max(abs(lo), abs(hi))

# Step 4 & 5: Build table with all formatting
gt = (
    GT(df, rowname_col=None)
    .fmt_number(columns=["open", "close"], decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=2, scale_values=False, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0)
    .fmt_number(columns=["high_gain", "high_loss"], decimals=2)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
    )
    .cols_label(
        open="Opening Price",
        close="Closing Price",
        pct_change="Monthly %",
        avg_volume="Avg Daily Vol",
        high_gain="Highest Daily Gain",
        high_loss="Highest Daily Loss",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# Apply band, stripe, frame
gt = band(gt, shade="light", hue="forest")
gt = stripe(gt)
gt = frame(gt)

# Add titles and footer notes
gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010-2015)",
        subtitle="Opening and closing prices, monthly percent change, trading volume, and daily extremes",
    )
    .tab_source_note("Monthly opening price is the first trading day's open; closing price is the last trading day's close. Percent change calculated as (close - open) / open.")
    .tab_source_note("Highest daily gain/loss represents the single largest intraday move within each month.")
)

finalize(gt, "table.png")
