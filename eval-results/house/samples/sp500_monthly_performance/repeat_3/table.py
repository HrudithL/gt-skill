import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the S&P 500 data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df_filtered = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values("date")

# Create monthly aggregates
monthly = df_filtered.groupby(df_filtered["date"].dt.to_period("M")).agg({
    "open": "first",
    "close": "last",
    "volume": "mean",
    "high": "max",
    "low": "min",
}).reset_index()

monthly.columns = ["month", "open", "close", "avg_volume", "month_high", "month_low"]

# Compute metrics
monthly["pct_change"] = ((monthly["close"] - monthly["open"]) / monthly["open"]) * 100

# For daily gains/losses within each month
def get_best_worst_days(group):
    dates = group["date"].dt.to_period("M")
    daily_change = group["close"].diff()
    best_day = daily_change.max()
    worst_day = daily_change.min()
    return pd.Series({
        "best_day_gain": best_day if best_day > 0 else np.nan,
        "worst_day_loss": worst_day if worst_day < 0 else np.nan,
    })

best_worst = df_filtered.groupby(df_filtered["date"].dt.to_period("M")).apply(get_best_worst_days).reset_index()
best_worst.columns = ["month", "best_day_gain", "worst_day_loss"]

# Merge
monthly = monthly.merge(best_worst, on="month")

# Convert month to a readable label
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
monthly = monthly[["month_label", "open", "close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"]]
monthly.columns = ["month", "open", "close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"]

# Create GT table
gt = GT(monthly, rowname_col="month")

# Header
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle=md("2010–2015: Opening price, closing price, percent change, daily volume, and single-day extremes"),
)

# Spanners for grouping
gt = gt.tab_spanner(label="Monthly Prices", columns=["open", "close"])
gt = gt.tab_spanner(label="Daily Extremes", columns=["best_day_gain", "worst_day_loss"])

# Spanner dividers (vertical separators)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="close"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="close"),
)

gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="avg_volume"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="avg_volume"),
)

# Format columns
gt = gt.fmt_number(columns=["open", "close"], decimals=2)
gt = gt.fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
gt = gt.fmt_number(columns=["best_day_gain", "worst_day_loss"], decimals=2)
gt = gt.fmt_percent(columns=["pct_change"], decimals=2, scale_values=False)

# Label columns
gt = gt.cols_label(
    open="Open",
    close="Close",
    pct_change="% Change",
    avg_volume="Avg Daily Volume",
    best_day_gain="Best Day Gain",
    worst_day_loss="Worst Day Loss",
)

# Column widths
gt = gt.cols_width(
    cases={
        "month": "110px",
        "open": "95px",
        "close": "95px",
        "pct_change": "95px",
        "avg_volume": "130px",
        "best_day_gain": "110px",
        "worst_day_loss": "110px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Color the percent change column (diverging)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Branding
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Missing values
gt = gt.sub_missing(columns=["best_day_gain", "worst_day_loss"], missing_text="—")

# Source notes
gt = gt.tab_source_note(
    source_note="Percent change represents the (close - open) / open for each month. Best day gain and worst day loss show the single largest daily move within the month (intra-month daily changes only)."
)
gt = gt.tab_source_note(source_note="Source: provided S&P 500 historical dataset.")

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
