import pandas as pd
import numpy as np
from great_tables import GT, loc
from gt_consistency import heatmap, band, stripe, stub_tint, frame, hairlines, finalize, PALETTE

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()
df = df.sort_values("date").reset_index(drop=True)

df["year_month"] = df["date"].dt.to_period("M")

monthly_data = []
for period, group in df.groupby("year_month"):
    group = group.sort_values("date").reset_index(drop=True)

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    avg_volume = group["volume"].mean()

    daily_changes = group["high"] - group["low"]
    highest_gain = daily_changes.max()
    worst_loss = daily_changes.min()

    monthly_data.append({
        "Month": period.strftime("%Y-%m"),
        "Open": opening_price,
        "Close": closing_price,
        "Change %": pct_change,
        "Avg Volume": avg_volume,
        "Best Day Gain": highest_gain,
        "Worst Day Loss": worst_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

lo_pct = float(np.nanmin(monthly_df[["Change %"]].to_numpy()))
hi_pct = float(np.nanmax(monthly_df[["Change %"]].to_numpy()))
lo_vol = float(np.nanmin(monthly_df[["Avg Volume"]].to_numpy()))
hi_vol = float(np.nanmax(monthly_df[["Avg Volume"]].to_numpy()))
lo_gain = float(np.nanmin(monthly_df[["Best Day Gain"]].to_numpy()))
hi_gain = float(np.nanmax(monthly_df[["Best Day Gain"]].to_numpy()))

gt = (
    GT(monthly_df, rowname_col="Month")
    .fmt_number(columns=["Open", "Close", "Best Day Gain", "Worst Day Loss"], decimals=2)
    .fmt_number(columns=["Avg Volume"], decimals=0)
    .fmt_number(columns=["Change %"], decimals=2)
)

gt = heatmap(gt, "Change %", kind="sequential", hue="neutral", domain=[lo_pct, hi_pct])
gt = heatmap(gt, "Avg Volume", kind="sequential", hue="neutral", domain=[lo_vol, hi_vol])
gt = heatmap(gt, "Best Day Gain", kind="sequential", hue="positive", domain=[lo_gain, hi_gain])

gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary (2010–2015)",
        subtitle="Opening/closing prices, monthly percent change, average daily volume, and highest single-day gain/loss"
    )
    .tab_source_note("Monthly percent change is calculated as (closing price − opening price) / opening price × 100. Best-day gain and worst-day loss represent the largest intraday high-low spread within each month.")
    .tab_source_note("Data source: S&P 500 historical prices (2010–2015)")
)

gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = hairlines(gt)
gt = finalize(gt)
