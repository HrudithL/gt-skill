import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: UNDERSTAND & CLEAN THE DATA
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date").reset_index(drop=True)

# Aggregate to monthly summaries
monthly_data = []
for year, month in df.groupby([df["date"].dt.year, df["date"].dt.month]).groups.keys():
    month_df = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]

    opening_price = month_df.iloc[0]["open"]
    closing_price = month_df.iloc[-1]["close"]
    pct_change = (closing_price - opening_price) / opening_price

    avg_volume = month_df["volume"].mean()

    # Highest single-day gain: max(close - open)
    daily_gains = month_df["close"] - month_df["open"]
    highest_gain = daily_gains.max()

    # Lowest single-day loss: min(close - open)
    lowest_loss = daily_gains.min()

    period = f"{year}-{month:02d}"

    monthly_data.append({
        "period": period,
        "open": opening_price,
        "close": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "highest_gain": highest_gain,
        "lowest_loss": lowest_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Step 2: ORGANIZE COLUMNS
# Stub: period (month), then numeric columns
# Order: open, close, pct_change, avg_volume, highest_gain, lowest_loss

# Step 3: BIG COLOR
# pct_change: diverging fill (RdYlGn, signed)
# avg_volume: sequential fill (Blues, neutral magnitude)
# highest_gain: sequential fill (Greens, "more is better")
# lowest_loss: sequential fill (Reds, "more is worse")

# Compute domains for data_color
pct_lo = float(np.nanmin(monthly_df[["pct_change"]].to_numpy()))
pct_hi = float(np.nanmax(monthly_df[["pct_change"]].to_numpy()))
pct_M = max(abs(pct_lo), abs(pct_hi))

vol_lo = float(np.nanmin(monthly_df[["avg_volume"]].to_numpy()))
vol_hi = float(np.nanmax(monthly_df[["avg_volume"]].to_numpy()))

gain_lo = float(np.nanmin(monthly_df[["highest_gain"]].to_numpy()))
gain_hi = float(np.nanmax(monthly_df[["highest_gain"]].to_numpy()))

loss_lo = float(np.nanmin(monthly_df[["lowest_loss"]].to_numpy()))
loss_hi = float(np.nanmax(monthly_df[["lowest_loss"]].to_numpy()))

gt = (
    GT(monthly_df, rowname_col="period")
    # Column labels
    .cols_label(
        open="Opening Price",
        close="Closing Price",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        highest_gain="Highest Daily Gain",
        lowest_loss="Lowest Daily Loss",
    )
    # Column widths
    .cols_width(cases={
        "period": "100px",
        "open": "120px",
        "close": "120px",
        "pct_change": "110px",
        "avg_volume": "140px",
        "highest_gain": "140px",
        "lowest_loss": "140px",
    })
    # Formatting
    .fmt_number(columns=["open", "close"], decimals=2, use_seps=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["highest_gain", "lowest_loss"], decimals=2, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=1, scale_values=False, force_sign=True)
    # BIG COLOR — Step 3
    # Percent change: diverging (RdYlGn, signed, symmetric domain)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_M, pct_M],
        truncate=False,
    )
    # Average volume: sequential (Blues, neutral magnitude)
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        truncate=False,
    )
    # Highest gain: sequential (Greens, "more is better")
    .data_color(
        columns=["highest_gain"],
        palette="Greens",
        domain=[gain_lo, gain_hi],
        truncate=False,
    )
    # Lowest loss: sequential (Reds, "more is worse")
    .data_color(
        columns=["lowest_loss"],
        palette="Reds",
        domain=[loss_lo, loss_hi],
        truncate=False,
    )
    # HEADING BAND — Step 4 (fixed navy band)
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle="2010–2015: Opening price, closing price, percent change, average daily volume, and daily extremes",
    )
    # SMALL COLOR POLISH — Step 5
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame (Step 5 global constant)
    .tab_options(
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
    # Compact layout padding (Step 5 global constant)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # TITLES & ANNOTATIONS — Step 6
    # Analytical caption: define the metrics
    .tab_source_note(
        source_note="Highest Daily Gain = maximum daily close − open within the month. Lowest Daily Loss = minimum daily close − open within the month."
    )
    # Source/provenance note
    .tab_source_note(
        source_note="Source: S&P 500 daily price data (sp500.csv)."
    )
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
