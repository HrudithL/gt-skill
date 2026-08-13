import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# STEP 1: Data cleaning
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])

# Filter to 2010-2015
df_raw = df_raw[(df_raw["date"].dt.year >= 2010) & (df_raw["date"].dt.year <= 2015)]

# Aggregate to monthly summaries
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

monthly = []
for period, group in df_raw.groupby("year_month"):
    group = group.sort_values("date")

    # Monthly: open = first day's open, close = last day's close
    month_open = group.iloc[0]["open"]
    month_close = group.iloc[-1]["close"]

    # Percent change
    pct_change = (month_close - month_open) / month_open

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Daily changes: high - low (intraday), and close - open
    group["daily_gain"] = group["high"] - group["low"]
    group["daily_change"] = group["close"] - group["open"]

    # Highest single-day gain (intraday high - low)
    best_day_gain = group["daily_gain"].max()

    # Worst single-day loss (minimum close - open, i.e., most negative)
    worst_day_loss = group["daily_change"].min()

    monthly.append({
        "period": str(period),
        "open": month_open,
        "close": month_close,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_gain": best_day_gain,
        "worst_loss": worst_day_loss,
    })

df = pd.DataFrame(monthly)

# Sort chronologically (should already be)
df = df.sort_values("period").reset_index(drop=True)

# STEP 2: Organize columns and structure
# Stub = period, measures in narrative order: open, close, pct_change, avg_volume, best_gain, worst_loss

# STEP 3: Big Color — four measures qualify
# (a) pct_change — diverging (signed, positive=good)
# (b) avg_volume — sequential magnitude (Blues)
# (c) best_gain — sequential magnitude (Blues)
# (d) worst_loss — actually minimum (most negative), but we want to highlight absolute magnitude
#     This is tricky: "worst loss" semantically means negative values. But in the data it's minimum (most negative).
#     For the table, we'll show worst_loss as-is (negative), and could color by absolute value or keep it plain.
#     Per the spec, we have 4 distinct dimensions. Let's color worst_loss too (Blues for magnitude).

# Compute domains for gradients
vol_cols = ["avg_volume"]
vol_lo = float(np.nanmin(df[vol_cols].to_numpy()))
vol_hi = float(np.nanmax(df[vol_cols].to_numpy()))

gain_cols = ["best_gain"]
gain_lo = float(np.nanmin(df[gain_cols].to_numpy()))
gain_hi = float(np.nanmax(df[gain_cols].to_numpy()))

loss_cols = ["worst_loss"]
loss_lo = float(np.nanmin(df[loss_cols].to_numpy()))
loss_hi = float(np.nanmax(df[loss_cols].to_numpy()))
loss_M = max(abs(loss_lo), abs(loss_hi))  # symmetric domain for worst loss (it's signed)

# pct_change diverging domain
pct_lo = float(np.nanmin(df["pct_change"].to_numpy()))
pct_hi = float(np.nanmax(df["pct_change"].to_numpy()))
pct_M = max(abs(pct_lo), abs(pct_hi))

# Build the GT
gt = GT(df, rowname_col="period")

# STEP 2+5: Format columns (Step 5 checklist)
gt = (
    gt
    .fmt_currency(columns=["open", "close"], decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=1, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["best_gain"], decimals=2)
    .fmt_number(columns=["worst_loss"], decimals=2)
)

# STEP 3: Big Color fills

# (a) Percent change — diverging RdYlGn (positive = good = green)
gt = gt.data_color(
    columns=["pct_change"],
    palette="RdYlGn",
    domain=[-pct_M, pct_M],
    truncate=False,
)

# (b) Average volume — sequential Blues
gt = gt.data_color(
    columns=["avg_volume"],
    palette="Blues",
    domain=[vol_lo, vol_hi],
    truncate=False,
    na_color="#808080",
)

# (c) Best daily gain — sequential Blues
gt = gt.data_color(
    columns=["best_gain"],
    palette="Blues",
    domain=[gain_lo, gain_hi],
    truncate=False,
    na_color="#808080",
)

# (d) Worst daily loss — signed, but we'll use diverging on the raw (negative) values
#     Actually, worst_loss is a minimum (negative), so let's use symmetric domain for clarity
gt = gt.data_color(
    columns=["worst_loss"],
    palette="RdYlGn",
    reverse=True,  # more negative = worse = red
    domain=[-loss_M, loss_M],
    truncate=False,
)

# STEP 4: Heading band
gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance (2010–2015)",
        subtitle="Summary metrics for each month: opening/closing prices, percent change, average daily volume, and daily trading range",
    )
    .tab_options(
        column_labels_font_weight="bold",
        table_font_size="11px",
        table_background_color="white",
        column_labels_background_color="#08306B",
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.column_labels(),
    )
)

# STEP 5: Small Color polish

# (a) Cell borders — hairline between rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    row_striping_background_color="#F6F6F6",
)

# (c) Row striping — apply by default (body is not 100% colored)
gt = gt.opt_row_striping()

# (d) Stub tint
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# Frame borders
gt = gt.tab_options(
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

# Compact layout
gt = gt.cols_width(
    cases={
        "period": "90px",
        "open": "100px",
        "close": "100px",
        "pct_change": "110px",
        "avg_volume": "130px",
        "best_gain": "110px",
        "worst_loss": "110px",
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

# STEP 6: Titles & Annotations (footer)
gt = (
    gt
    .tab_source_note(
        source_note="Monthly percent change is (close − open) ÷ open. Best day gain is the intraday high − low. Worst day loss is the minimum (close − open) within the month, representing the largest single-day decline."
    )
    .tab_source_note(
        source_note="Data: S&P 500 daily prices, 2010–2015."
    )
)

# STEP 7: Render
gt.gtsave("table.png", expand=15, zoom=2.0, vwidth=1000, vheight=800)
