import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read the data
df = pd.read_csv("./sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df = df.sort_values("date")

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")

# Calculate monthly metrics
monthly = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date")

    open_price = group.iloc[0]["open"]
    close_price = group.iloc[-1]["close"]
    pct_change = (close_price - open_price) / open_price if open_price != 0 else np.nan

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Daily gains and losses within the month
    group_daily = group.sort_values("date").reset_index(drop=True)
    daily_changes = []
    for i in range(len(group_daily)):
        if i == 0:
            prev_close = group_daily.iloc[i]["open"]
        else:
            prev_close = group_daily.iloc[i-1]["close"]
        daily_change = group_daily.iloc[i]["close"] - prev_close
        daily_changes.append(daily_change)

    max_gain = max(daily_changes) if daily_changes else np.nan
    max_loss = min(daily_changes) if daily_changes else np.nan

    monthly.append({
        "year_month": str(period),
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "max_gain": max_gain,
        "max_loss": max_loss,
    })

monthly_df = pd.DataFrame(monthly)

# Build the table
gt = (
    GT(monthly_df, rowname_col="year_month")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle=md("Daily metrics by month, 2010–2015")
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="open", decimals=2)
    .fmt_number(columns="close", decimals=2)
    .fmt_percent(columns="pct_change", decimals=2, force_sign=True)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_number(columns="max_gain", decimals=2)
    .fmt_number(columns="max_loss", decimals=2)
)

gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        "open": "Open",
        "close": "Close",
        "pct_change": "% Change",
        "avg_volume": "Avg Daily Volume",
        "max_gain": "Max Daily Gain",
        "max_loss": "Max Daily Loss",
    }
)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "year_month": "95px",
        "open": "85px",
        "close": "85px",
        "pct_change": "95px",
        "avg_volume": "130px",
        "max_gain": "110px",
        "max_loss": "110px",
    }
)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap to percent change (diverging measure)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Header band, striping, stub tint, frame, hairlines
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes and frame
gt = (
    gt.tab_source_note(
        source_note="% Change is the month-over-month percent change from opening to closing price. Max Daily Gain and Loss are intramonth daily point changes."
    )
    .tab_source_note(source_note="Source: S&P 500 historical daily price data.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
