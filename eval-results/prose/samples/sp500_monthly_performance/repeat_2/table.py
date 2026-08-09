import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

# Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Sort by date
df = df.sort_values("date").reset_index(drop=True)

# Extract year-month
df["year_month"] = df["date"].dt.to_period("M")

# Group by month
monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date")
    open_price = group["open"].iloc[0]
    close_price = group["close"].iloc[-1]
    pct_change = (close_price - open_price) / open_price

    # Daily gains and losses
    group["daily_gain"] = group["high"] - group["low"]
    group["daily_change"] = group["close"] - group["open"]

    max_gain = group["daily_gain"].max()
    max_loss = group["daily_change"].min()

    avg_volume = group["volume"].mean()

    monthly_data.append({
        "Month": str(period),
        "Open": open_price,
        "Close": close_price,
        "Pct Change": pct_change,
        "Avg Volume": avg_volume,
        "Max Gain": max_gain,
        "Max Loss": max_loss,
    })

df_monthly = pd.DataFrame(monthly_data)

# Compute symmetric domain for diverging fill
cols = ["Pct Change"]
lo = float(np.nanmin(df_monthly[cols].to_numpy()))
hi = float(np.nanmax(df_monthly[cols].to_numpy()))
M = max(abs(lo), abs(hi))

# Build the table
gt = (
    GT(df_monthly, rowname_col="Month")
    .fmt_currency(columns=["Open", "Close"], decimals=2, currency="USD")
    .fmt_percent(columns=["Pct Change"], decimals=1, force_sign=True)
    .fmt_currency(columns=["Max Gain", "Max Loss"], decimals=2, currency="USD")
    .fmt_number(columns=["Avg Volume"], decimals=0, use_seps=True)
    .data_color(
        columns=["Pct Change"],
        palette="RdYlGn",
        reverse=False,
        domain=[-M, M],
        truncate=False,
    )
    .tab_options(
        # Stub tint (grey)
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
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
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_header(
        title="S&P 500 Monthly Performance (2010–2015)",
        subtitle=md("Opening price, closing price, percent change, average daily volume, and daily high-low range by month. Percent change is monthly close-minus-open divided by open."),
    )
)

gt.gtsave("table.png", expand=15)
