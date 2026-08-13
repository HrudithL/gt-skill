"""S&P 500 monthly performance summary, 2010-2015.

Data: sp500.csv (S&P 500 daily prices, daily OHLCV)
Story: Monthly aggregation showing opening price, closing price, percent change,
       average daily volume, highest single-day gain, and worst single-day loss
       for each month from 2010 through 2015.
"""
import numpy as np
import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to 2010-2015.
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df["month"] = df["date"].dt.to_period("M")

# Compute monthly metrics.
monthly = df.groupby("month").agg(
    open=("open", "first"),
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
    volume=("volume", "mean"),
).reset_index()

# Percent change from open to close.
monthly["pct_change"] = monthly["close"] / monthly["open"] - 1

# Intraday high-low = highest single-day gain/loss within the month.
monthly["best_day_gain"] = df.groupby("month").apply(
    lambda x: (x["high"] - x["open"]).max()
).values

monthly["worst_day_loss"] = df.groupby("month").apply(
    lambda x: (x["low"] - x["close"]).min()
).values

# Month label for the stub.
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

# Select and reorder columns for the table.
monthly = monthly[[
    "month_label",
    "open",
    "close",
    "pct_change",
    "volume",
    "best_day_gain",
    "worst_day_loss",
]].reset_index(drop=True)

# Data-driven domains for the two signed columns (both positive and negative).
pct_m = float(np.nanmax(np.abs(monthly["pct_change"].to_numpy())))
gain_m = float(np.nanmax(np.abs(monthly["best_day_gain"].to_numpy())))
loss_m = float(np.nanmax(np.abs(monthly["worst_day_loss"].to_numpy())))

# Percent change and gain/loss are signed measures, good/bad directions.
# Percent change: positive = good (green), negative = bad (red).
# Gain and loss are directionally opposite: gain is positive/good, loss is negative/bad.

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 — Monthly Performance Summary (2010–2015)",
        subtitle="Opening & closing prices, percent change, average daily volume, and intraday range",
    )
    # Column spanners to group related measures.
    .tab_spanner(label="Price ($)", columns=["open", "close"])
    .tab_spanner(label="Performance", columns=["pct_change", "best_day_gain", "worst_day_loss"])
    .cols_label(
        open="Open",
        close="Close",
        pct_change="% Change",
        volume="Avg Daily Vol",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss",
    )
    # Format prices as currency.
    .fmt_currency(columns=["open", "close"], currency="USD", decimals=2)
    # Format average volume as number with thousands separators.
    .fmt_number(columns=["volume"], decimals=0, use_seps=True)
    # Percent change with forced sign.
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    # Best day gain and worst day loss as price changes with forced sign.
    .fmt_currency(columns=["best_day_gain", "worst_day_loss"], currency="USD", decimals=2, force_sign=True)
    # Data color — percent change with diverging RdYlGn (red/bad ← → green/good).
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_m, pct_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Data color — best day gain (green, sequential, positive is good).
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[0, gain_m],
        na_color="#808080",
        truncate=False,
    )
    # Data color — worst day loss (red, sequential, but inverted domain so negative is worse).
    # Since worst_day_loss is negative, map the absolute worst to the darkest red.
    .data_color(
        columns=["worst_day_loss"],
        palette="Reds",
        domain=[loss_m, 0],  # inverted so most negative = darkest
        na_color="#808080",
        truncate=False,
    )
    # Align numeric columns to the right.
    .cols_align(
        align="right",
        columns=["open", "close", "pct_change", "volume", "best_day_gain", "worst_day_loss"],
    )
    # Column-group vertical dividers.
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="close"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="close"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="worst_day_loss"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="worst_day_loss"),
    )
    # Heading band — fixed branding navy, bold labels, white text.
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex.
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping.
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
    # Column widths.
    .cols_width(cases={
        "month_label": "80px",
        "open": "90px",
        "close": "90px",
        "pct_change": "90px",
        "volume": "110px",
        "best_day_gain": "110px",
        "worst_day_loss": "110px",
    })
    # Padding.
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Footer notes.
    .tab_source_note(
        source_note=(
            "Percent change measures the monthly return from opening to closing price. "
            "Best day gain is the maximum intraday high vs. open; worst day loss is the "
            "minimum intraday low vs. close. Both reflect the largest single-day price move "
            "within each month, not the month-long trend."
        )
    )
    .tab_source_note(source_note="Source: S&P 500 daily OHLCV, 2010–2015.")
)

gt.gtsave("table.png", zoom=2.0, expand=15)
