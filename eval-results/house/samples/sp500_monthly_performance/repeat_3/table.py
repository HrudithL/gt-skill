import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE,
    frame,
    hairlines,
    finalize,
    band,
    stripe,
    heatmap,
    humanize_labels,
)

# Read the S&P 500 data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df_filtered = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

# Sort by date
df_filtered = df_filtered.sort_values("date").reset_index(drop=True)

# Extract year and month
df_filtered["year_month"] = df_filtered["date"].dt.to_period("M")

# Group by year-month to compute monthly metrics
monthly_data = []
for year_month, group in df_filtered.groupby("year_month"):
    group = group.sort_values("date")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = (closing_price - opening_price) / opening_price
    avg_volume = group["volume"].mean()

    # Highest single-day gain (max close-to-close change)
    group["daily_change"] = group["close"].diff()
    group["daily_pct_change"] = group["close"].pct_change()

    max_daily_gain = group["daily_pct_change"].max()
    max_daily_loss = group["daily_pct_change"].min()

    monthly_data.append({
        "month": year_month.strftime("%b %Y"),
        "open": opening_price,
        "close": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "max_daily_gain": max_daily_gain,
        "max_daily_loss": max_daily_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Create GT object
gt = (
    GT(monthly_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Opening price, closing price, monthly return, volume, and extreme daily moves — 2010–2015"),
    )
    .tab_stubhead(label="Month")
    .fmt_currency(columns=["open", "close"], decimals=2)
    .fmt_percent(columns=["pct_change", "max_daily_gain", "max_daily_loss"], decimals=2, force_sign=True)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
)

gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        "open": "Opening Price",
        "close": "Closing Price",
        "pct_change": "Monthly Change %",
        "avg_volume": "Avg Daily Volume",
        "max_daily_gain": "Max Daily Gain %",
        "max_daily_loss": "Max Daily Loss %",
    },
)

# Set column widths
gt = gt.cols_width(
    cases={
        "month": "110px",
        "open": "120px",
        "close": "120px",
        "pct_change": "130px",
        "avg_volume": "140px",
        "max_daily_gain": "130px",
        "max_daily_loss": "130px",
    }
)

# Set padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmaps for the key measures: pct_change (diverging) and max_daily_gain/loss (diverging)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")
gt = heatmap(gt, ["max_daily_gain", "max_daily_loss"], kind="diverging", hue="default")

# Heading band with navy color
gt = band(gt, hue="navy")

# Striping (body is not 100% heatmapped so stripe applies)
gt = stripe(gt)

# Add source notes
gt = gt.tab_source_note(
    source_note="Monthly Change % and daily extremes are calculated as percentage change; Max Daily Loss % is typically negative."
)
gt = gt.tab_source_note(source_note="Source: S&P 500 historical daily data, 2010–2015.")

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Render
finalize(gt)
