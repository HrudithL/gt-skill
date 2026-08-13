import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Calculate intraday gains/losses for each day
df["daily_gain"] = df["high"] - df["open"]
df["daily_loss"] = df["low"] - df["open"]

# Group by year-month
df["month"] = df["date"].dt.strftime("%Y-%m")
monthly_groups = df.groupby("month")

# Build monthly summary
summary = []
for month_key, group in monthly_groups:
    month_obj = datetime.strptime(month_key, "%Y-%m")
    summary.append({
        "month": month_key,
        "opening_price": group["open"].iloc[0],
        "closing_price": group["close"].iloc[-1],
        "pct_change": (group["close"].iloc[-1] - group["open"].iloc[0]) / group["open"].iloc[0],
        "avg_volume": group["volume"].mean(),
        "best_day_gain": group["daily_gain"].max(),
        "worst_day_loss": group["daily_loss"].min(),
    })

monthly_df = pd.DataFrame(summary)

# Step 2: Organize columns and prepare for display
display_df = monthly_df[["month", "opening_price", "closing_price", "pct_change",
                         "avg_volume", "best_day_gain", "worst_day_loss"]].copy()

# Step 3: Compute domains for Big Color fills
pct_lo = float(np.nanmin(display_df["pct_change"].to_numpy()))
pct_hi = float(np.nanmax(display_df["pct_change"].to_numpy()))
pct_M = max(abs(pct_lo), abs(pct_hi))

vol_lo = float(np.nanmin(display_df["avg_volume"].to_numpy()))
vol_hi = float(np.nanmax(display_df["avg_volume"].to_numpy()))

gain_lo = float(np.nanmin(display_df["best_day_gain"].to_numpy()))
gain_hi = float(np.nanmax(display_df["best_day_gain"].to_numpy()))

loss_lo = float(np.nanmin(display_df["worst_day_loss"].to_numpy()))
loss_hi = float(np.nanmax(display_df["worst_day_loss"].to_numpy()))

# Build the table
gt = (
    GT(display_df, rowname_col="month")
    # Step 4: Heading band (fixed branding)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening Price, Closing Price, Monthly Return, Daily Volume, and Daily Extremes"
    )
    .tab_stubhead(label="Month")
    # Column labels
    .cols_label(
        opening_price="Opening Price",
        closing_price="Closing Price",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss"
    )
    # Step 5: Format columns per semantic type
    .fmt_number(columns=["opening_price", "closing_price", "best_day_gain", "worst_day_loss"], decimals=2)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    # Step 3: Big Color fills
    # Percent change: diverging (RdYlGn, symmetric domain)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_M, pct_M],
        truncate=False,
        na_color="#808080"
    )
    # Average volume: sequential Blues (neutral magnitude)
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        truncate=False,
        na_color="#808080"
    )
    # Best day gain: sequential Greens (more is better)
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[gain_lo, gain_hi],
        truncate=False,
        na_color="#808080"
    )
    # Worst day loss: sequential Reds magnitude (magnitude of loss, "more is worse")
    .data_color(
        columns=["worst_day_loss"],
        palette="Reds",
        domain=[loss_lo, loss_hi],
        truncate=False,
        na_color="#808080"
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Column label text color (white on navy band)
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels()
    )
    # (c) Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    # Heading band background (navy)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # Frame: boxed border on all four sides
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#E8E8E8",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#E8E8E8",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#E8E8E8",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#E8E8E8",
        table_border_right_width="1px",
    )
    # Step 6: Titles & annotations (footer - two separate calls)
    .tab_source_note(
        "% Change: (Closing Price – Opening Price at month start) / Opening Price at month start. "
        "Best Day Gain: maximum intraday gain (High – Open) within the month. "
        "Worst Day Loss: minimum intraday loss (Low – Open) within the month."
    )
    .tab_source_note("Source: S&P 500 daily price and volume data, 2010–2015")
)

# Step 7: Render and verify
gt.gtsave("table.png", zoom=2)
print("Table rendered to table.png")
