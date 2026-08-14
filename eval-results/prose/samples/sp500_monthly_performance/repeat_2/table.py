import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Load and clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Group by year-month
df["year_month"] = df["date"].dt.to_period("M")
grouped = df.groupby("year_month")

# Calculate monthly metrics
monthly_data = []
for period, group in grouped:
    # Sort by date to ensure correct opening/closing prices
    group = group.sort_values("date")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    avg_daily_volume = group["volume"].mean()

    # Daily gain/loss within the month (close - open for each day)
    group["daily_change"] = group["close"] - group["open"]
    best_day_gain = group["daily_change"].max()
    worst_day_loss = group["daily_change"].min()

    monthly_data.append({
        "Month": str(period),
        "Opening Price": opening_price,
        "Closing Price": closing_price,
        "Percent Change": pct_change,
        "Average Daily Volume": avg_daily_volume,
        "Best Day Gain": best_day_gain,
        "Worst Day Loss": worst_day_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Create GT table
gt = (
    GT(monthly_df, rowname_col="Month")
    .fmt_number(columns=["Opening Price", "Closing Price"], decimals=2)
    .fmt_number(columns=["Percent Change"], decimals=2)
    .fmt_number(columns=["Average Daily Volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["Best Day Gain", "Worst Day Loss"], decimals=2)
    .data_color(
        columns=["Percent Change"],
        palette="RdYlGn",
        domain=[monthly_df["Percent Change"].min(), monthly_df["Percent Change"].max()],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Average Daily Volume"],
        palette="Blues",
        domain=[monthly_df["Average Daily Volume"].min(), monthly_df["Average Daily Volume"].max()],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Best Day Gain"],
        palette="Greens",
        domain=[0, monthly_df["Best Day Gain"].max()],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Worst Day Loss"],
        palette="Reds",
        domain=[monthly_df["Worst Day Loss"].min(), 0],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening/Closing Prices, Percent Change, Volume, and Daily Gains/Losses"
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.borders(sides="all", color="#E8E8E8", weight="1px"),
        locations=loc.body(),
    )
    .tab_source_note(
        "Monthly percent change calculated as (closing price − opening price) / opening price × 100. "
        "Best/worst day gain/loss is the largest single-day change (close − open) within each month."
    )
    .tab_source_note(
        "Data source: S&P 500 daily closing data (sp500.csv)"
    )
)

gt.gtsave("table.png")
print("Table saved to table.png")
