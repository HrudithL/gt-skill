import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Read and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"] >= "2010-01-01") & (df["date"] <= "2015-12-31")]
df = df.sort_values("date").reset_index(drop=True)

# Create month-year column for grouping
df["month"] = df["date"].dt.to_period("M")

# Compute daily pct_change across full series (continuous)
df["daily_pct_change"] = df["close"].pct_change()

# Group by month and aggregate
monthly = df.groupby("month").agg({
    "open": "first",
    "close": "last",
    "volume": "mean",
    "daily_pct_change": ["min", "max"],  # smallest (loss), largest (gain) single-day change
}).reset_index()

monthly.columns = ["month", "open", "close", "avg_volume", "max_daily_loss", "max_daily_gain"]

# Compute monthly percent change (close - open) / open
monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

# Reorder columns
monthly = monthly[["month", "open", "close", "pct_change", "avg_volume", "max_daily_loss", "max_daily_gain"]]

# Format month as "Mon YYYY" string for stub
monthly["month_str"] = monthly["month"].dt.strftime("%b %Y")

# Drop the period column, keep only the formatted string
monthly = monthly.drop("month", axis=1)
monthly = monthly.rename(columns={"month_str": "Month"})

# Prepare display dataframe with Month as the stub
display_df = monthly.copy()

# Compute domain for pct_change (required for data_color)
lo = float(np.nanmin(display_df[["pct_change"]].to_numpy()))
hi = float(np.nanmax(display_df[["pct_change"]].to_numpy()))

# Build the table
gt = (
    GT(display_df, rowname_col="Month")
    # Step 3: Big Color — percent change gradient (ordered magnitude, sequential Blues)
    .data_color(
        columns=["pct_change"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 5(a): Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5(c): Row striping (≥10 rows, body not fully filled)
    .opt_row_striping()
    # Step 5(d): Stub tint (stub exists, grey default since Big Color is Blues)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5(e): Formatting per column
    .fmt_number(columns=["open", "close"], decimals=2, use_seps=True)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["pct_change", "max_daily_loss", "max_daily_gain"], decimals=2)
    .sub_missing(columns=["open", "close", "pct_change", "avg_volume", "max_daily_loss", "max_daily_gain"], missing_text="—")
    # Step 4: Heading band (light, since we have Big Color)
    .tab_options(
        heading_background_color="#EAF0F6",
    )
    # Step 6: Titles and source notes
    .tab_header(
        title="S&P 500 Monthly Performance Summary, 2010–2015",
        subtitle="Opening price, closing price, percent change, average daily volume, and daily extremes per month"
    )
    .tab_source_note(
        source_note="Single-day gain/loss use a continuous day-over-day change across the full historical series, "
                    "not reset at each month's start."
    )
    .tab_source_note(source_note="Source: S&P 500 daily stock data.")
)

# Column labels
gt = (
    gt.cols_label(
        open="Open",
        close="Close",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        max_daily_loss="Largest Single-Day Loss",
        max_daily_gain="Largest Single-Day Gain",
    )
)

# Step 7: Render
gt.gtsave("table.png")
