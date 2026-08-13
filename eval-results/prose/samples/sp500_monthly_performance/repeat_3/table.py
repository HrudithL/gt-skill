"""S&P 500 Monthly Performance Summary (2010-2015).

Data: sp500.csv (daily prices and volume)
Story: Monthly aggregates showing opening/closing prices, percent change,
       average daily volume, and best/worst single-day moves within each month.
"""
import pandas as pd
import numpy as np
from great_tables import GT, html, loc, style

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Add daily change for best/worst calculations
df["daily_change"] = df["close"] - df["open"]

# Monthly aggregation
monthly_data = []
for period, group in df.groupby(df["date"].dt.to_period("M")):
    monthly_data.append({
        "month_label": str(period),
        "open_price": group["open"].iloc[0],
        "close_price": group["close"].iloc[-1],
        "avg_volume": group["volume"].mean(),
        "best_day_gain": group["daily_change"].max(),
        "worst_day_loss": group["daily_change"].min(),
    })

monthly = pd.DataFrame(monthly_data)

# Percent change: (close - open) / open * 100
monthly["pct_change"] = ((monthly["close_price"] - monthly["open_price"]) / monthly["open_price"]) * 100

# Reorder columns
monthly = monthly[[
    "month_label",
    "open_price",
    "close_price",
    "pct_change",
    "avg_volume",
    "best_day_gain",
    "worst_day_loss",
]]

# Compute domains for colored measures
# pct_change: signed, needs symmetric diverging domain
pct_min = float(np.nanmin(monthly["pct_change"].to_numpy()))
pct_max = float(np.nanmax(monthly["pct_change"].to_numpy()))
pct_domain_bound = max(abs(pct_min), abs(pct_max))
pct_domain = [-pct_domain_bound, pct_domain_bound]

# avg_volume: neutral magnitude (Blues)
vol_lo = float(np.nanmin(monthly["avg_volume"].to_numpy()))
vol_hi = float(np.nanmax(monthly["avg_volume"].to_numpy()))

# best_day_gain: magnitude, positive values (Greens)
best_lo = float(np.nanmin(monthly["best_day_gain"].to_numpy()))
best_hi = float(np.nanmax(monthly["best_day_gain"].to_numpy()))

# worst_day_loss: signed, typically negative (Reds with reverse for interpretation)
worst_lo = float(np.nanmin(monthly["worst_day_loss"].to_numpy()))
worst_hi = float(np.nanmax(monthly["worst_day_loss"].to_numpy()))
worst_domain_bound = max(abs(worst_lo), abs(worst_hi))
worst_domain = [-worst_domain_bound, worst_domain_bound]

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="Opening/closing prices, returns, trading volume, and intra-month volatility, 2010–2015",
    )
    .cols_label(
        open_price="Opening Price",
        close_price="Closing Price",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        best_day_gain="Best Single-Day Gain",
        worst_day_loss="Worst Single-Day Loss",
    )
    # Formatting: prices (currency), percent (with force_sign for signed), volume (number), daily moves (number with sign)
    .fmt_currency(columns=["open_price", "close_price"], currency="USD", decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=1, scale_values=False, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["best_day_gain", "worst_day_loss"], decimals=2, force_sign=True)
    # Data color: pct_change (signed, RdYlGn), avg_volume (magnitude, Blues),
    # best_day_gain (positive magnitude, Greens), worst_day_loss (signed, RdYlGn with reverse)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=pct_domain,
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[best_lo, best_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .data_color(
        columns=["worst_day_loss"],
        palette="RdYlGn",
        domain=worst_domain,
        reverse=True,
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_align(align="right", columns=["open_price", "close_price", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"])
    # Heading band — fixed branding navy, bold labels, white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex, unconditional whenever a stub exists
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping — default on every table
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
        "month_label": "100px",
        "open_price": "120px",
        "close_price": "120px",
        "pct_change": "100px",
        "avg_volume": "130px",
        "best_day_gain": "130px",
        "worst_day_loss": "130px",
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
        source_note=html(
            "Percent change is calculated as (closing price − opening price) / opening price × 100. "
            "Best/worst single-day gains and losses show the largest daily close-open deltas within each month."
        )
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily price and volume data, 2010–2015."
    )
)

gt.gtsave("table.png", zoom=2.0, expand=15)
