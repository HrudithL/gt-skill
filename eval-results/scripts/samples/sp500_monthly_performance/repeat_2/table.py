"""S&P 500 monthly performance summary, 2010-2015."""
import numpy as np
import pandas as pd
from great_tables import GT, loc, style
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df["year_month"] = df["date"].dt.to_period("M")

# Monthly aggregation: compute statistics per month
monthly = df.groupby("year_month").agg(
    open=("open", "first"),
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
    volume=("volume", "mean"),
).reset_index()

# Compute percent change (close - open) / open
monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

# Compute daily intraday gain/loss per month (high - low)
monthly["daily_range"] = df.groupby("year_month").apply(
    lambda x: (x["high"] - x["low"]).max()
).reset_index(drop=True)

# Compute best single-day gain (max(high - open) within the month)
monthly["best_day_gain"] = df.groupby("year_month").apply(
    lambda x: (x["high"] - x["open"]).max()
).reset_index(drop=True)

# Compute worst single-day loss (min(low - open) within the month, i.e., most negative)
monthly["worst_day_loss"] = df.groupby("year_month").apply(
    lambda x: (x["low"] - x["open"]).min()
).reset_index(drop=True)

# Format display label: "Mon YYYY"
monthly["month_label"] = monthly["year_month"].dt.strftime("%b %Y")

# Select and reorder columns for display
monthly = monthly[
    ["month_label", "open", "close", "pct_change", "volume", "best_day_gain", "worst_day_loss"]
].reset_index(drop=True)

# Compute domains for color fills
pct_change_m = float(np.nanmax(np.abs(monthly["pct_change"].to_numpy())))
volume_min = float(np.nanmin(monthly["volume"].to_numpy()))
volume_max = float(np.nanmax(monthly["volume"].to_numpy()))
best_day_gain_max = float(np.nanmax(monthly["best_day_gain"].to_numpy()))
worst_day_loss_min = float(np.nanmin(monthly["worst_day_loss"].to_numpy()))

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015: Opening price, closing price, monthly percent change, average daily volume, and daily extremes",
    )
    .tab_spanner(label="Price", columns=["open", "close"])
    .tab_spanner(label="Monthly Summary", columns=["pct_change", "volume"])
    .tab_spanner(label="Daily Range ($)", columns=["best_day_gain", "worst_day_loss"])
    .cols_label(
        open="Open",
        close="Close",
        pct_change="% Change",
        volume="Avg Volume",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss",
    )
    # Formatting
    .fmt_currency(columns=["open", "close", "best_day_gain", "worst_day_loss"], currency="USD", decimals=2)
    .fmt_number(columns=["volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    # Color fills: percent change (diverging) and average volume (sequential)
)

gt = heatmap(gt, "pct_change", kind="diverging", hue="default", domain=[-pct_change_m, pct_change_m])
gt = heatmap(gt, "volume", kind="sequential", hue="neutral", domain=[volume_min, volume_max])

# Column alignment
gt = gt.cols_align(align="right", columns=["open", "close", "pct_change", "volume", "best_day_gain", "worst_day_loss"])

# Column-group vertical dividers at spanner seams
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="close"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="close"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="volume"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="volume"),
    )
)

# Compact layout
gt = gt.cols_width(cases={
    "month_label": "75px",
    "open": "85px",
    "close": "85px",
    "pct_change": "80px",
    "volume": "110px",
    "best_day_gain": "100px",
    "worst_day_loss": "100px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Footer notes
gt = (
    gt.tab_source_note(
        source_note=(
            "Best day gain = largest intraday high within the month; worst day loss = largest intraday decline. "
            "Monthly % change = (close − open) ÷ open. Average volume is the mean daily trading volume across the month."
        )
    )
    .tab_source_note(source_note="Source: S&P 500 daily closing prices, 1950–2015.")
)

# Apply branding and polish helpers
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = hairlines(gt)

finalize(gt, "table.png")
