"""S&P 500 Monthly Performance Summary 2010-2015.

Story: Monthly opening/closing prices, percent change, average daily volume,
       and best/worst single-day intraday moves across 6 years.
"""
import numpy as np
import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df["month"] = df["date"].dt.to_period("M")

# Monthly aggregation: opening (first day), closing (last day), high/low for intraday range,
# volume for average daily volume, and highest/lowest close for day-over-day moves
monthly = df.groupby("month").agg(
    open=("open", "first"),
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
    volume=("volume", "mean"),
).reset_index()

# Percent change: (close - open) / open
monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

# Intraday best/worst single day: highest intraday gain (high - open on best day) and worst loss (low - open on worst day)
# For each month, find the day with the best intraday high and the day with the worst intraday low
def best_intraday_gain(group):
    # Best gain is the highest (high - close) on any day in the month
    return (group["high"] - group["close"]).max()

def worst_intraday_loss(group):
    # Worst loss is the lowest (low - close) on any day in the month
    return (group["low"] - group["close"]).min()

intraday = df.groupby("month").apply(lambda g: pd.Series({
    "best_gain": best_intraday_gain(g),
    "worst_loss": worst_intraday_loss(g),
})).reset_index()

monthly = monthly.merge(intraday, on="month")

# Reorder and clean up
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
monthly = monthly[[
    "month_label", "open", "close", "pct_change", "volume", "best_gain", "worst_loss"
]].reset_index(drop=True)

# Compute domains for coloring
# Percent change is signed, positive = good (gains)
pct_m = float(np.nanmax(np.abs(monthly["pct_change"].to_numpy())))

# Volume, best_gain, worst_loss are ordered magnitudes
vol_lo = float(np.nanmin(monthly["volume"].to_numpy()))
vol_hi = float(np.nanmax(monthly["volume"].to_numpy()))
gain_lo = float(np.nanmin(monthly["best_gain"].to_numpy()))
gain_hi = float(np.nanmax(monthly["best_gain"].to_numpy()))
loss_lo = float(np.nanmin(monthly["worst_loss"].to_numpy()))
loss_hi = float(np.nanmax(monthly["worst_loss"].to_numpy()))

# Find best and worst months for the caption
best_month_idx = monthly["pct_change"].idxmax()
best_month = monthly.loc[best_month_idx, "month_label"]
best_pct = monthly.loc[best_month_idx, "pct_change"]

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 — Monthly Performance Summary 2010-2015",
        subtitle="Opening/closing prices, percent change, average daily volume, and best/worst intraday moves",
    )
    # Spanners group columns logically
    .tab_spanner(label="Price ($)", columns=["open", "close"])
    .tab_spanner(label="Performance", columns=["pct_change", "volume", "best_gain", "worst_loss"])
    .cols_label(
        open="Opening",
        close="Closing",
        pct_change="% Change",
        volume="Avg Daily Vol",
        best_gain="Best Day Gain",
        worst_loss="Worst Day Loss",
    )
    # Formatting
    .fmt_currency(columns=["open", "close"], currency="USD", decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    .fmt_number(columns=["volume"], decimals=0, use_seps=True)
    .fmt_currency(columns=["best_gain", "worst_loss"], currency="USD", decimals=2)
    # Color the percent change (signed, positive = good)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_m, pct_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Color the volume (neutral magnitude)
    .data_color(
        columns=["volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Color best day gain (positive is good)
    .data_color(
        columns=["best_gain"],
        palette="Greens",
        domain=[gain_lo, gain_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Color worst day loss (negative is worse, so use Reds for magnitude)
    .data_color(
        columns=["worst_loss"],
        palette="Reds",
        domain=[loss_lo, loss_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_align(align="right", columns=["open", "close", "pct_change", "volume", "best_gain", "worst_loss"])
    # Column-group vertical dividers
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.body(columns="close"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.column_labels(columns="close"))
    # Heading band — fixed branding navy
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    .cols_width(cases={
        "month_label": "110px", "open": "95px", "close": "95px", "pct_change": "90px",
        "volume": "110px", "best_gain": "105px", "worst_loss": "105px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_source_note(
        source_note=(
            f"Best month: {best_month} ({best_pct:+.2%}). "
            "Percent change is (closing - opening) / opening. "
            "Best day gain and worst day loss are the highest intraday high and lowest intraday low relative to close, respectively."
        )
    )
    .tab_source_note(source_note="Source: S&P 500 daily prices, 2010-2015.")
)

gt.gtsave("table.png", zoom=2.0, expand=15)
