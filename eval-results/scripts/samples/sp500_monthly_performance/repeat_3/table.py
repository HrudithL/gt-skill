import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date").reset_index(drop=True)

df["year_month"] = df["date"].dt.to_period("M")

monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date")
    open_price = group.iloc[0]["open"]
    close_price = group.iloc[-1]["close"]
    pct_change = ((close_price - open_price) / open_price) * 100
    avg_volume = group["volume"].mean()

    group["daily_gain"] = group["high"] - group["low"]
    max_gain = group["daily_gain"].max()

    group["daily_loss"] = group["open"] - group["close"]
    max_loss = group["daily_loss"].max()

    monthly_data.append({
        "Month": str(period),
        "Open": open_price,
        "Close": close_price,
        "Change %": pct_change,
        "Avg Volume": avg_volume,
        "Max Gain": max_gain,
        "Max Loss": max_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

gt = (
    GT(monthly_df, rowname_col="Month")
    .fmt_currency(columns=["Open", "Close"], currency="USD", decimals=2)
    .fmt_number(columns=["Avg Volume"], decimals=0)
    .fmt_number(columns=["Max Gain", "Max Loss"], decimals=2)
    .fmt_number(columns=["Change %"], decimals=2)
    .tab_header(
        title=md("**S&P 500 Monthly Performance Summary**"),
        subtitle=md("2010–2015 — Opening and closing prices, monthly percent change, average daily volume, and intraday extremes"),
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

gt = heatmap(gt, columns=["Change %"], kind="diverging", hue="default")
gt = band(gt, shade="light", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = frame(gt)
gt = finalize(gt)

gt.gtsave("table.png")
