import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv("sp500.csv", parse_dates=["date"])
df = df.sort_values("date")

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

filtered_df = df[(df["year"] >= 2010) & (df["year"] <= 2015)].copy()

monthly_data = []
for (year, month), group in filtered_df.groupby(["year", "month"]):
    month_label = pd.Timestamp(year=year, month=month, day=1).strftime("%B %Y")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    avg_volume = group["volume"].mean()

    group["daily_gain"] = group["close"] - group["open"]
    highest_gain = group["daily_gain"].max()
    highest_loss = group["daily_gain"].min()

    monthly_data.append({
        "month": month_label,
        "opening_price": opening_price,
        "closing_price": closing_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "highest_gain": highest_gain,
        "highest_loss": highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

gt = GT(summary_df, rowname_col="month")
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle=md("2010–2015: opening and closing prices, monthly percent change, average daily volume, and daily extremes"),
)
gt = gt.fmt_number(columns="opening_price", decimals=2)
gt = gt.fmt_number(columns="closing_price", decimals=2)
gt = gt.fmt_number(columns="pct_change", decimals=2, force_sign=True)
gt = gt.fmt_number(columns="avg_volume", decimals=0, use_seps=True)
gt = gt.fmt_number(columns="highest_gain", decimals=2, force_sign=True)
gt = gt.fmt_number(columns="highest_loss", decimals=2, force_sign=True)

gt = gt.cols_label(
    opening_price="Opening Price",
    closing_price="Closing Price",
    pct_change="% Change",
    avg_volume="Avg Daily Volume",
    highest_gain="Highest Single-Day Gain",
    highest_loss="Highest Single-Day Loss",
)

gt = gt.cols_width(
    cases={
        "month": "130px",
        "opening_price": "110px",
        "closing_price": "110px",
        "pct_change": "100px",
        "avg_volume": "130px",
        "highest_gain": "140px",
        "highest_loss": "140px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = gt.sub_missing(missing_text="—")

gt = (
    gt.tab_source_note(
        source_note="Percent change represents the monthly opening to closing price change. Daily extremes are the highest single-day gains and losses within each month."
    )
    .tab_source_note(source_note="Source: provided S&P 500 dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
