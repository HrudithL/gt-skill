import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: UNDERSTAND AND CLEAN DATA
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date").reset_index(drop=True)

# Aggregate to monthly: opening (first day), closing (last day), volume stats, intraday gains/losses
monthly = (
    df.groupby(df["date"].dt.to_period("M"))
    .agg({
        "open": "first",
        "close": "last",
        "volume": "mean",
        "high": "max",
        "low": "min",
    })
    .reset_index()
)
monthly.columns = ["period", "open", "close", "avg_volume", "month_high", "month_low"]

# Compute percent change
monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

# Compute daily gains/losses within each month
daily_gains_losses = []
for period in monthly["period"]:
    period_df = df[df["date"].dt.to_period("M") == period]
    period_df["daily_gain"] = period_df["high"] - period_df["open"]
    period_df["daily_loss"] = period_df["open"] - period_df["low"]
    daily_gains_losses.append({
        "period": period,
        "max_daily_gain": period_df["daily_gain"].max(),
        "max_daily_loss": period_df["daily_loss"].max(),
    })

gains_losses_df = pd.DataFrame(daily_gains_losses)
monthly = monthly.merge(gains_losses_df, on="period")

# Format period label for display
monthly["month_label"] = monthly["period"].astype(str)

# Reorder and select final columns
monthly = monthly[["month_label", "open", "close", "pct_change", "avg_volume", "max_daily_gain", "max_daily_loss"]]
monthly.columns = ["Month", "Open", "Close", "Pct_Change", "Avg_Volume", "Max_Daily_Gain", "Max_Daily_Loss"]

# Ensure all numeric columns are float64
for col in ["Open", "Close", "Pct_Change", "Avg_Volume", "Max_Daily_Gain", "Max_Daily_Loss"]:
    monthly[col] = monthly[col].astype("float64")

# Step 2: ORGANIZE COLUMNS
# Month is the stub; all other columns are measures
# Percent change is signed (diverging fill), daily gains/losses and volume are magnitudes

# Step 3: BIG COLOR
# Percent change: signed measure (diverging palette RdYlGn, positive=good)
# Max daily gain: neutral magnitude (Blues)
# Max daily loss: neutral magnitude (Blues)
# Avg volume: neutral magnitude (Blues)

# Compute symmetric domain for percent change
pct_cols = ["Pct_Change"]
pct_lo = float(np.nanmin(monthly[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(monthly[pct_cols].to_numpy()))
pct_M = max(abs(pct_lo), abs(pct_hi))

# Compute domain for daily gain (magnitude, sequential)
gain_cols = ["Max_Daily_Gain"]
gain_lo = float(np.nanmin(monthly[gain_cols].to_numpy()))
gain_hi = float(np.nanmax(monthly[gain_cols].to_numpy()))

# Compute domain for daily loss (magnitude, sequential)
loss_cols = ["Max_Daily_Loss"]
loss_lo = float(np.nanmin(monthly[loss_cols].to_numpy()))
loss_hi = float(np.nanmax(monthly[loss_cols].to_numpy()))

# Compute domain for volume (magnitude, sequential)
vol_cols = ["Avg_Volume"]
vol_lo = float(np.nanmin(monthly[vol_cols].to_numpy()))
vol_hi = float(np.nanmax(monthly[vol_cols].to_numpy()))

# Step 4 & 5: Build the table with formatting and styling
gt = (
    GT(monthly, rowname_col="Month")
    # Formatting per column
    .fmt_currency(columns=["Open", "Close"], decimals=2)
    .fmt_percent(columns=["Pct_Change"], decimals=2, force_sign=True)
    .fmt_number(columns=["Avg_Volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["Max_Daily_Gain", "Max_Daily_Loss"], decimals=2)
    # Big Color: percent change (signed/diverging)
    .data_color(
        columns="Pct_Change",
        palette="RdYlGn",
        domain=[-pct_M, pct_M],
        reverse=False,
        truncate=False,
    )
    # Big Color: daily gain (magnitude/sequential)
    .data_color(
        columns="Max_Daily_Gain",
        palette="Blues",
        domain=[gain_lo, gain_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color: daily loss (magnitude/sequential)
    .data_color(
        columns="Max_Daily_Loss",
        palette="Blues",
        domain=[loss_lo, loss_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color: average volume (magnitude/sequential)
    .data_color(
        columns="Avg_Volume",
        palette="Blues",
        domain=[vol_lo, vol_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed branding)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5a: Body row hairlines and 5c: Row striping
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
    )
    .opt_row_striping()
    # Step 5d: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Missing value handling
    .sub_missing(columns=monthly.columns.tolist(), missing_text="—")
    # Step 6: Titles and annotations
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010-2015)",
        subtitle="Opening price, closing price, percent change, and daily volatility metrics by month",
    )
    .tab_source_note(
        source_note="Percent change = (Close − Open) / Open. Max daily gain = intraday high − opening price. Max daily loss = opening price − intraday low. All data from sp500.csv."
    )
    .tab_source_note(
        source_note="Source: S&P 500 historical price data, 2010–2015."
    )
)

# Step 7: Render
gt.gtsave("table.png")
