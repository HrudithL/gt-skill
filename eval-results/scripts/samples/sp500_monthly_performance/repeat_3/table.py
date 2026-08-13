import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, md, style, loc
from gt_consistency import frame, hairlines, finalize, heatmap, band, stripe, stub_tint, PALETTE

# Step 1: Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Filter to 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]
df_raw = df_raw.sort_values("date")

# Step 1: Calculate monthly statistics
monthly_data = []
for year_month, group in df_raw.groupby(df_raw["date"].dt.to_period("M")):
    group = group.sort_values("date")

    open_price = group.iloc[0]["open"]
    close_price = group.iloc[-1]["close"]
    pct_change = (close_price - open_price) / open_price if open_price > 0 else np.nan

    # Calculate daily gains/losses within the month
    daily_change = group["close"] - group["open"]
    best_day_gain = daily_change.max()
    worst_day_loss = daily_change.min()

    avg_volume = group["volume"].mean()

    monthly_data.append({
        "period": str(year_month),
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day_gain": best_day_gain,
        "worst_day_loss": worst_day_loss,
    })

df = pd.DataFrame(monthly_data)

# Step 2: Organize columns and prepare for GT
# We'll show: period (stub), open, close, pct_change (colored, diverging),
# avg_volume (colored, sequential), best_day_gain, worst_day_loss

gt = (
    GT(df, rowname_col="period")
    # Step 5: Formatting per column (e)
    .fmt_currency(columns=["open", "close"], decimals=2, use_seps=True)
    .fmt_percent(columns="pct_change", decimals=2, force_sign=True)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_currency(columns=["best_day_gain", "worst_day_loss"], decimals=2, use_seps=True)
    .sub_missing(missing_text="—")
)

# Step 3: Big Color — heatmap for percent change (diverging, signed)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Step 3: Big Color — heatmap for avg_volume (sequential, neutral magnitude)
gt = heatmap(gt, "avg_volume", kind="sequential", hue="neutral")

# Step 4: Heading band (fixed navy)
gt = band(gt)

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = hairlines(gt)

# Step 5: Column widths for compact layout
gt = gt.cols_width(cases={
    "period": "100px",
    "open": "110px",
    "close": "110px",
    "pct_change": "120px",
    "avg_volume": "130px",
    "best_day_gain": "130px",
    "worst_day_loss": "130px",
})

# Step 5: Padding (branding constants)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 5: Cell borders (hairlines already applied via hairlines() helper)
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015 Summary Statistics"
    )
    .tab_source_note(
        source_note="Percent change is calculated as (closing price − opening price) ÷ opening price for each month. "
                   "Best-day gain and worst-day loss represent the largest single-day price movement within each month."
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily OHLC data (sp500.csv)"
    )
)

# Step 5: Frame (boxed border)
gt = frame(gt)

# Step 7: Render
finalize(gt, "table.png")
