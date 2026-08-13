import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import band, frame, finalize, heatmap, stripe, stub_tint, hairlines

# Step 1: Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Sort by date ascending
df = df.sort_values("date")

# Extract year-month and calculate monthly metrics
df["year_month"] = df["date"].dt.to_period("M")

monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date")

    open_price = group.iloc[0]["open"]
    close_price = group.iloc[-1]["close"]
    percent_change = ((close_price - open_price) / open_price) * 100

    avg_volume = group["volume"].mean()

    # Daily gain: close - open for each day
    daily_gains = group["close"].values - group["open"].values
    highest_daily_gain = daily_gains.max()
    worst_daily_loss = daily_gains.min()

    monthly_data.append({
        "Month": str(period),
        "Open": open_price,
        "Close": close_price,
        "Percent Change": percent_change,
        "Avg Daily Volume": avg_volume,
        "Highest Daily Gain": highest_daily_gain,
        "Worst Daily Loss": worst_daily_loss,
    })

summary_df = pd.DataFrame(monthly_data)

# Step 2: Organize columns and set up GT
gt = GT(summary_df, rowname_col="Month")

# Step 3: Format numbers
gt = (
    gt
    .fmt_number(columns="Open", decimals=2)
    .fmt_number(columns="Close", decimals=2)
    .fmt_percent(columns="Percent Change", decimals=2, scale_values=False, force_sign=True)
    .fmt_number(columns="Avg Daily Volume", decimals=0, use_seps=True)
    .fmt_number(columns="Highest Daily Gain", decimals=2)
    .fmt_number(columns="Worst Daily Loss", decimals=2)
)

# Step 3: Apply Big Color heatmaps
# Percent Change: diverging (signed), centered at 0
lo = float(np.nanmin(summary_df[["Percent Change"]].to_numpy()))
hi = float(np.nanmax(summary_df[["Percent Change"]].to_numpy()))
domain_pct = [-max(abs(lo), abs(hi)), max(abs(lo), abs(hi))]

gt = gt.data_color(
    columns="Percent Change",
    palette="RdYlGn",
    domain=domain_pct,
    truncate=False,
    na_color="#808080",
)

# Avg Daily Volume: sequential (magnitude)
lo_vol = float(np.nanmin(summary_df[["Avg Daily Volume"]].to_numpy()))
hi_vol = float(np.nanmax(summary_df[["Avg Daily Volume"]].to_numpy()))

gt = gt.data_color(
    columns="Avg Daily Volume",
    palette="Blues",
    domain=[lo_vol, hi_vol],
    truncate=False,
    na_color="#808080",
)

# Highest Daily Gain: sequential (positive values, more is better)
lo_gain = float(np.nanmin(summary_df[["Highest Daily Gain"]].to_numpy()))
hi_gain = float(np.nanmax(summary_df[["Highest Daily Gain"]].to_numpy()))

gt = gt.data_color(
    columns="Highest Daily Gain",
    palette="Greens",
    domain=[lo_gain, hi_gain],
    truncate=False,
    na_color="#808080",
)

# Worst Daily Loss: sequential (negative values, more negative is worse)
lo_loss = float(np.nanmin(summary_df[["Worst Daily Loss"]].to_numpy()))
hi_loss = float(np.nanmax(summary_df[["Worst Daily Loss"]].to_numpy()))

gt = gt.data_color(
    columns="Worst Daily Loss",
    palette="Reds",
    domain=[lo_loss, hi_loss],
    truncate=False,
    na_color="#808080",
)

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Apply small color checklist
gt = stripe(gt)
gt = stub_tint(gt)
gt = hairlines(gt)

# Column widths and padding
gt = (
    gt
    .cols_width(cases={
        "Month": "140px",
        "Open": "110px",
        "Close": "110px",
        "Percent Change": "130px",
        "Avg Daily Volume": "140px",
        "Highest Daily Gain": "140px",
        "Worst Daily Loss": "130px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015",
    )
    .tab_source_note(
        md("Daily gain/loss calculated as closing price − opening price for each trading day. Highest single-day gain and worst single-day loss reflect the maximum and minimum daily price changes within each month.")
    )
    .tab_source_note(
        md("Data: S&P 500 daily closing prices (sp500.csv)")
    )
)

# Step 7: Frame and finalize
gt = frame(gt)

gt = finalize(gt)
