import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Load and clean data
df = pd.read_csv("sp500.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

# Extract year and month
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# Group by year-month to calculate monthly metrics
monthly_data = []
for (year, month), group in df.groupby(["year", "month"], sort=True):
    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = (closing_price - opening_price) / opening_price if opening_price > 0 else np.nan
    avg_volume = group["volume"].mean()

    # Intraday gain/loss (high - low for each day)
    group["intraday_range"] = group["high"] - group["low"]
    best_gain = group["intraday_range"].max()
    worst_loss = -group["intraday_range"].min()  # negative value

    monthly_data.append({
        "Period": f"{year}-{month:02d}",
        "Open": opening_price,
        "Close": closing_price,
        "Percent Change": pct_change,
        "Avg Daily Volume": avg_volume,
        "Best Day Gain": best_gain,
        "Worst Day Loss": worst_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Filter to 2010-2015
monthly_df["year"] = monthly_df["Period"].str[:4].astype(int)
monthly_df = monthly_df[(monthly_df["year"] >= 2010) & (monthly_df["year"] <= 2015)].reset_index(drop=True)
monthly_df = monthly_df.drop("year", axis=1)

# Calculate domain for percent change (symmetric around 0)
pct_cols = ["Percent Change"]
lo = float(np.nanmin(monthly_df[pct_cols].to_numpy()))
hi = float(np.nanmax(monthly_df[pct_cols].to_numpy()))
M = max(abs(lo), abs(hi))

# Build the table
gt = (
    GT(monthly_df, rowname_col="Period")
    # Format columns
    .fmt_currency(columns=["Open", "Close", "Best Day Gain"], decimals=2, use_seps=True)
    .fmt_currency(columns=["Worst Day Loss"], decimals=2, use_seps=True)
    .fmt_number(columns=["Avg Daily Volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["Percent Change"], decimals=2, force_sign=True)
    # Color percent change with diverging palette
    .data_color(
        columns=["Percent Change"],
        palette="RdYlGn",
        domain=[-M, M],
        truncate=False,
    )
    # Heading band
    .tab_options(
        heading_background_color="#08306B",
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Body row hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Borders
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
    # Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Compact layout
    .cols_width(cases={
        "Open": "110px",
        "Close": "110px",
        "Percent Change": "130px",
        "Avg Daily Volume": "140px",
        "Best Day Gain": "120px",
        "Worst Day Loss": "120px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening and Closing Prices, Returns, Volume, and Intraday Range",
    )
    # Annotations
    .tab_source_note(
        source_note="Percent change is calculated from monthly opening to closing price. Best day gain and worst day loss represent the maximum intraday range (high–low) for each trading day within the month."
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily historical data."
    )
    .sub_missing(columns=monthly_df.columns.tolist(), missing_text="—")
)

gt.gtsave("table.png", expand=15)
