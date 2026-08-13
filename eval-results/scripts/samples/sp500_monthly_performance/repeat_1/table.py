import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("sp500.csv")

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

df_filtered = df[(df["year"] >= 2010) & (df["year"] <= 2015)].copy()

monthly_data = []
for (year, month), group in df_filtered.groupby(["year", "month"]):
    group = group.sort_values("date")

    open_price = group["open"].iloc[0]
    close_price = group["close"].iloc[-1]
    pct_change = ((close_price - open_price) / open_price)

    avg_volume = group["volume"].mean()

    intraday_gains = group["high"] - group["low"]
    highest_gain = intraday_gains.max()

    daily_changes = group["close"].diff()
    worst_loss = daily_changes.min()

    year_month_str = f"{year}-{month:02d}"

    monthly_data.append({
        "period": year_month_str,
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day_gain": highest_gain,
        "worst_day_loss": worst_loss,
    })

df_summary = pd.DataFrame(monthly_data)

gt = (
    GT(df_summary, rowname_col="period")
    .cols_label(
        open="Open",
        close="Close",
        pct_change="% Change",
        avg_volume="Avg Daily Volume",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss",
    )
    .fmt_number(columns=["open", "close"], decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=0, compact=True)
    .fmt_number(columns=["best_day_gain", "worst_day_loss"], decimals=2)
)

gt = heatmap(gt, "pct_change", kind="diverging", hue="default")
gt = heatmap(gt, ["best_day_gain", "worst_day_loss"], kind="sequential", hue="neutral")
gt = heatmap(gt, "avg_volume", kind="sequential", hue="neutral")

gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

gt = (
    gt.tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening price, closing price, monthly return, and daily volatility metrics"
    )
    .tab_source_note(
        md("**Analytical caption:** Percent change is calculated as (close − open) / open. Best day gain is the largest intraday gain (high − low) in each month. Worst day loss is the largest single-day decline (close.diff) in each month.")
    )
    .tab_source_note(
        md("**Source:** S&P 500 historical price data, 2010–2015")
    )
)

finalize(gt, "table.png")
