import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint

# Step 1: Read and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df = df.sort_values("date").reset_index(drop=True)

# Compute daily percent change for identifying best/worst single-day moves
df["daily_pct_change"] = df["close"].pct_change() * 100

# Group by year-month to compute monthly aggregates
df["year_month"] = df["date"].dt.to_period("M")

monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date").reset_index(drop=True)

    opening = group["open"].iloc[0]
    closing = group["close"].iloc[-1]
    pct_change = ((closing - opening) / opening) * 100
    avg_volume = group["volume"].mean()

    # Single-day movements: high vs previous close, low vs previous close
    # For the first day, compare intraday high/low to opening
    daily_changes = group["daily_pct_change"].dropna()
    best_day_gain = daily_changes.max() if len(daily_changes) > 0 else np.nan
    worst_day_loss = daily_changes.min() if len(daily_changes) > 0 else np.nan

    monthly_data.append({
        "month": pd.Timestamp(period.to_timestamp()),
        "open": opening,
        "close": closing,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day_gain": best_day_gain,
        "worst_day_loss": worst_day_loss,
    })

monthly_df = pd.DataFrame(monthly_data)
monthly_df["month_label"] = monthly_df["month"].dt.strftime("%b %Y")
monthly_df = monthly_df[[
    "month_label", "open", "close", "pct_change", "avg_volume",
    "best_day_gain", "worst_day_loss"
]]

# Step 2: Organize columns with stub (month_label as row identifier)
# Step 3: Big Color decision — pct_change is a signed measure (gains/losses)
# Use diverging palette with symmetric domain
cols_signed = ["pct_change", "best_day_gain", "worst_day_loss"]
lo = float(np.nanmin(monthly_df[cols_signed].to_numpy()))
hi = float(np.nanmax(monthly_df[cols_signed].to_numpy()))
M = max(abs(lo), abs(hi))

# avg_volume is a magnitude (sequential positive)
vol_min = float(monthly_df["avg_volume"].min())
vol_max = float(monthly_df["avg_volume"].max())

gt = (
    GT(monthly_df, rowname_col="month_label")
    .cols_label(
        open="Open",
        close="Close",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss",
    )
    .tab_spanner(
        label="Price",
        columns=["open", "close"]
    )
    .tab_spanner(
        label="Monthly Performance",
        columns=["pct_change", "best_day_gain", "worst_day_loss"]
    )
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening/closing prices, monthly change, and single-day extremes",
    )
    # Format prices as currency
    .fmt_currency(columns=["open", "close"], currency="USD", decimals=2)
    # Format percent changes with signs
    .fmt_percent(columns=["pct_change", "best_day_gain", "worst_day_loss"], decimals=2, force_sign=True)
    # Format volume as integer
    .fmt_integer(columns=["avg_volume"])
    # Apply diverging color to signed measures (% change + best/worst days)
    # all three share the same domain since they're all percent changes
    .data_color(
        columns=["pct_change", "best_day_gain", "worst_day_loss"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
    )
    # Apply sequential color to volume (Blues for neutral magnitude)
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_min, vol_max],
    )
    # Align prices right, volumes right, month label left
    .cols_align(align="left", columns=["month_label"])
    .cols_align(align="right", columns=["open", "close", "avg_volume"])
    # Step 4: Heading band — has Big Color, so use washed tint (forest)
    # Step 5: Small Color polish
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
    )
)

gt = band(gt, shade="light", hue="forest")
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")
gt = frame(gt)
gt = finalize(gt, zoom=2.0, expand=15)
