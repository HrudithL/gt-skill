import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Sort by date ascending
df = df.sort_values("date").reset_index(drop=True)

# Compute daily gain/loss as percentage change from prior day
df["daily_pct_change"] = df["close"].pct_change()

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")
grouped = df.groupby("year_month")

# Aggregate monthly data
monthly_data = []
for period, group in grouped:
    month_str = period.strftime("%b %Y")
    opening = group.iloc[0]["open"]
    closing = group.iloc[-1]["close"]
    pct_change = ((closing - opening) / opening) * 100
    avg_volume = group["volume"].mean()

    # Compute highest single-day gain and loss
    # Gain: highest positive daily percent change
    daily_changes = group["daily_pct_change"].dropna()
    if len(daily_changes) > 0:
        highest_gain = daily_changes.max() * 100
        highest_loss = daily_changes.min() * 100
    else:
        highest_gain = 0
        highest_loss = 0

    monthly_data.append({
        "month": month_str,
        "open": opening,
        "close": closing,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "highest_gain": highest_gain,
        "highest_loss": highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

# Step 2: Organize columns and create GT
gt = (
    GT(summary_df, rowname_col="month")
    .fmt_number(columns=["open", "close"], decimals=2)
    .fmt_number(columns=["pct_change", "highest_gain", "highest_loss"], decimals=2)
    .fmt_number(columns=["avg_volume"], decimals=0)
    .cols_label(
        open="Opening",
        close="Closing",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        highest_gain="Highest Daily Gain %",
        highest_loss="Highest Daily Loss %",
    )
)

# Step 3: Apply Big Color to the signed measures (percent change and daily gains/losses)
# Percent change is a signed measure
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Daily gains/losses are paired signed measures in one domain
gt = heatmap(gt, ["highest_gain", "highest_loss"], kind="diverging", hue="default")

# Step 4: Apply heading band (light band due to Big Color presence)
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color polish
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# Apply striping and stub tint
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Step 6: Add titles
gt = (
    gt
    .tab_header(
        title=md("**S&P 500 Monthly Performance**"),
        subtitle=md("Monthly aggregates from daily data, 2010–2015"),
    )
    .tab_source_note(
        "Source: Daily S&P 500 closing prices and volumes")
)

# Step 7: Apply frame and render
gt = frame(gt)
finalize(gt, "table.png")
