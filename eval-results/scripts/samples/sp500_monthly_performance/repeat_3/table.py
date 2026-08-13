"""S&P 500 monthly performance summary, 2010–2015.

Story: Six years of monthly performance metrics — opening/closing prices,
       returns, volume, and intraday range — to show volatility and trends
       across the period.
"""
import numpy as np
import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv("sp500.csv", parse_dates=["date"]).sort_values("date")

# Restrict to 2010–2015.
period = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
period["month"] = period["date"].dt.to_period("M")

# Month aggregation: opening on first day, closing on last day, volume average,
# intraday range (high - low) on the day with the largest gain/loss.
monthly = period.groupby("month", observed=True).agg(
    open_price=("open", "first"),
    close_price=("close", "last"),
    high_all=("high", "max"),
    low_all=("low", "min"),
    volume=("volume", "mean"),
)

# Month-over-month return (percent change from open to close).
monthly["pct_change"] = (monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]

# Highest single-day intraday gain within the month: (high - low) on that day,
# computed as the max daily range (high - low) for any day in the month.
daily_ranges = period.copy()
daily_ranges["intra_range"] = daily_ranges["high"] - daily_ranges["low"]
max_gain_per_month = daily_ranges.groupby("month")["intra_range"].max()
monthly["max_daily_gain"] = monthly.index.map(max_gain_per_month)

# For "highest gain" and "lowest loss" — these are intraday, not close-to-close.
# The largest intraday swing (high - low) is the max_daily_gain above.
# For the worst day (largest intraday loss), it's the same metric — we show
# the largest intraday range as both gain and loss (the range itself).
# Alternatively: best day is the day with highest (close - open), worst day is
# the day with lowest (close - open). Let me use that definition.

best_day_per_month = daily_ranges.groupby("month").apply(
    lambda g: (g["close"] - g["open"]).max()
)
worst_day_per_month = daily_ranges.groupby("month").apply(
    lambda g: (g["close"] - g["open"]).min()
)

monthly["best_day_gain"] = monthly.index.map(best_day_per_month)
monthly["worst_day_loss"] = monthly.index.map(worst_day_per_month)

monthly = monthly.reset_index()
monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
monthly = monthly[[
    "month_label", "open_price", "close_price", "pct_change",
    "volume", "best_day_gain", "worst_day_loss"
]].reset_index(drop=True)

# Compute data-driven domains for color fills.
# Percent change: signed, positive-is-good (returns). Symmetric domain.
pct_lo = float(np.nanmin(monthly["pct_change"].to_numpy()))
pct_hi = float(np.nanmax(monthly["pct_change"].to_numpy()))
pct_m = max(abs(pct_lo), abs(pct_hi))

# Volume: neutral magnitude (sequential, Blues).
vol_lo = float(np.nanmin(monthly["volume"].to_numpy()))
vol_hi = float(np.nanmax(monthly["volume"].to_numpy()))

# Best day gain: magnitude, positive-is-good (Greens).
best_lo = float(np.nanmin(monthly["best_day_gain"].to_numpy()))
best_hi = float(np.nanmax(monthly["best_day_gain"].to_numpy()))

# Worst day loss: signed, negative-is-good (below zero is better). But the data
# is negative or zero, so we can use a diverging fill with reversed orientation.
worst_lo = float(np.nanmin(monthly["worst_day_loss"].to_numpy()))
worst_hi = float(np.nanmax(monthly["worst_day_loss"].to_numpy()))
worst_m = max(abs(worst_lo), abs(worst_hi))

# Best and worst day: use sequential on the ranges (magnitudes).
best_worst_lo = float(np.nanmin(
    np.concatenate([
        monthly["best_day_gain"].to_numpy(),
        np.abs(monthly["worst_day_loss"].to_numpy())
    ])
))
best_worst_hi = float(np.nanmax(
    np.concatenate([
        monthly["best_day_gain"].to_numpy(),
        np.abs(monthly["worst_day_loss"].to_numpy())
    ])
))

# Summary stats for annotations.
best_month = monthly.loc[monthly["pct_change"].idxmax(), "month_label"]
best_pct = monthly["pct_change"].max()
year_return_2015 = monthly[monthly["month_label"].str.contains("2015")]["pct_change"].sum()

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015: opening price, closing price, returns, volume, and daily ranges",
    )
    # Spanners organize columns by type: prices, returns/volume, intraday ranges.
    .tab_spanner(label="Price ($)", columns=["open_price", "close_price"])
    .tab_spanner(label="Performance", columns=["pct_change", "volume"])
    .tab_spanner(label="Daily Extremes ($)", columns=["best_day_gain", "worst_day_loss"])
    .cols_label(
        open_price="Open",
        close_price="Close",
        pct_change="Return %",
        volume="Avg Volume",
        best_day_gain="Best Day",
        worst_day_loss="Worst Day",
    )
    # Format columns by semantic type.
    .fmt_currency(columns=["open_price", "close_price"], currency="USD", decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    .fmt_number(columns=["volume"], decimals=0, use_seps=True)
    .fmt_currency(columns=["best_day_gain", "worst_day_loss"], currency="USD", decimals=2)
    # Color the performance metrics: percent change (signed return) and volume (magnitude).
    # Percent change: diverging, signed, positive-is-good.
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_m, pct_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Volume: sequential magnitude (Blues).
    .data_color(
        columns=["volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Best day and worst day: both are magnitude ranges. Best day (positive) gets Greens.
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[0, best_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Worst day: the magnitude of loss. Show as absolute value with Reds (higher loss = worse = red).
    .data_color(
        columns=["worst_day_loss"],
        palette="Reds",
        domain=[worst_lo, 0],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_align(align="right", columns=[
        "open_price", "close_price", "pct_change", "volume", "best_day_gain", "worst_day_loss"
    ])
    # Column-group vertical dividers at spanner seams.
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
               locations=loc.body(columns="close_price"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
               locations=loc.column_labels(columns="close_price"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
               locations=loc.body(columns="volume"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
               locations=loc.column_labels(columns="volume"))
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
    .cols_width(cases={
        "month_label": "95px",
        "open_price": "95px", "close_price": "95px",
        "pct_change": "95px", "volume": "110px",
        "best_day_gain": "110px", "worst_day_loss": "110px",
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
            f"Return % is (close − open) ÷ open for the month. Best Day and Worst Day represent "
            f"the largest single-day intraday range (high − low) and the smallest single-day close−open "
            f"change within each month, respectively. Avg Volume is the mean daily volume across all trading days."
        )
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily closing prices, 2010–2015."
    )
)

gt.gtsave("table.png", zoom=2.0, expand=15)
