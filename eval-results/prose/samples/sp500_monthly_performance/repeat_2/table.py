import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Group by year and month to compute monthly metrics
df["year_month"] = df["date"].dt.to_period("M")

monthly_stats = []
for period, group in df.groupby("year_month"):
    year, month = period.year, period.month
    period_str = period.strftime("%b %Y")

    # Opening price (first trading day of month)
    open_price = group.iloc[0]["open"]

    # Closing price (last trading day of month)
    close_price = group.iloc[-1]["close"]

    # Percent change
    pct_change = (close_price - open_price) / open_price

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Highest single-day gain (high - low within a day)
    daily_range = group["high"] - group["low"]
    highest_gain = daily_range.max()

    # Highest single-day loss (intraday low to high, as negative)
    highest_loss = -daily_range.max()  # Stored as negative for diverging fill

    monthly_stats.append({
        "Period": period_str,
        "Opening Price": open_price,
        "Closing Price": close_price,
        "Monthly % Change": pct_change,
        "Avg Daily Volume": avg_volume,
        "Highest Daily Gain": highest_gain,
        "Highest Daily Loss": highest_loss,
    })

monthly_df = pd.DataFrame(monthly_stats)

# Step 2: Organize columns - Period is the stub
# Step 3: Big Color - Monthly % Change is signed, use diverging fill
# Compute symmetric domain for diverging fill
cols_pct = ["Monthly % Change"]
lo = float(np.nanmin(monthly_df[cols_pct].to_numpy()))
hi = float(np.nanmax(monthly_df[cols_pct].to_numpy()))
M = max(abs(lo), abs(hi))

gt = (
    GT(monthly_df, rowname_col="Period")
    .fmt_currency(
        columns=["Opening Price", "Closing Price"],
        currency="USD",
        decimals=2,
        use_seps=True,
    )
    .fmt_percent(
        columns=["Monthly % Change"],
        decimals=2,
        force_sign=True,
    )
    .fmt_number(
        columns=["Avg Daily Volume"],
        decimals=0,
        use_seps=True,
    )
    .fmt_currency(
        columns=["Highest Daily Gain", "Highest Daily Loss"],
        currency="USD",
        decimals=2,
        use_seps=True,
    )
    .data_color(
        columns=["Monthly % Change"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
    )

    # Step 4: Heading band - light because we have Big Color
    .tab_options(
        column_labels_background_color="#EAF0F6",
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
    # Frame
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
    # (c) Row striping - 72 rows of data, so striping applies
    .opt_row_striping()
    # (d) Stub tint - Navy washed tint to match Big Color
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) sub_missing for any NA values
    .sub_missing(
        missing_text="—",
    )

    # Step 6: Titles and annotations
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening price, closing price, monthly return, volume, and daily extremes",
    )
    .tab_stubhead(label="Month")
)

# Add source notes (f)
gt = (
    gt.tab_source_note(
        source_note="Highest daily gain and loss represent the maximum intraday range (high minus low) within each calendar month."
    )
    .tab_source_note(
        source_note="Source: S&P 500 historical daily data (sp500.csv)."
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
