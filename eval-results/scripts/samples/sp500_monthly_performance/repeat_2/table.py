import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, band, stripe, stub_tint, heatmap, PALETTE

df = pd.read_csv("sp500.csv", parse_dates=["date"])

df["date"] = pd.to_datetime(df["date"])
df["year_month"] = df["date"].dt.to_period("M")

monthly = []
for period, group in df.groupby("year_month"):
    if group["date"].dt.year.min() < 2010 or group["date"].dt.year.min() > 2015:
        continue

    sorted_group = group.sort_values("date").reset_index(drop=True)

    open_price = sorted_group["open"].iloc[0]
    close_price = sorted_group["close"].iloc[-1]
    pct_change = (close_price - open_price) / open_price if open_price != 0 else 0

    avg_volume = sorted_group["volume"].mean()

    sorted_group["daily_change"] = sorted_group["close"].pct_change()
    best_gain = sorted_group["daily_change"].max()
    worst_loss = sorted_group["daily_change"].min()

    monthly.append({
        "month": period,
        "open": open_price,
        "close": close_price,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_gain": best_gain,
        "worst_loss": worst_loss,
    })

monthly_df = pd.DataFrame(monthly)
monthly_df = monthly_df[(monthly_df["month"].dt.year >= 2010) & (monthly_df["month"].dt.year <= 2015)].reset_index(drop=True)
monthly_df["month_label"] = monthly_df["month"].dt.strftime("%b %Y")

table_df = monthly_df[["month_label", "open", "close", "pct_change", "avg_volume", "best_gain", "worst_loss"]].copy()
table_df.columns = ["month", "open", "close", "pct_change", "avg_volume", "best_gain", "worst_loss"]

gt = (
    GT(table_df, rowname_col="month")
    .cols_label(
        open="Opening Price",
        close="Closing Price",
        pct_change="Monthly Change %",
        avg_volume="Avg Daily Volume",
        best_gain="Best Single-Day Gain %",
        worst_loss="Worst Single-Day Loss %",
    )
    .fmt_currency(columns=["open", "close"], currency="USD", decimals=2)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["pct_change", "best_gain", "worst_loss"], decimals=1, force_sign=True)
    .sub_missing(columns=["open", "close", "avg_volume", "best_gain", "worst_loss", "pct_change"], missing_text="—")
)

cols_to_color = ["pct_change", "best_gain", "worst_loss"]
lo = float(np.nanmin(table_df[cols_to_color].to_numpy()))
hi = float(np.nanmax(table_df[cols_to_color].to_numpy()))
M = max(abs(lo), abs(hi))

gt = heatmap(gt, cols_to_color, kind="diverging", hue="default", domain=[-M, M])

gt = band(gt, shade="light", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = frame(gt)

gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015",
    )
    .tab_source_note(
        source_note="Single-day gain/loss use a continuous day-over-day change across the full daily series, "
                     "not reset at each month's start."
    )
    .tab_source_note(source_note="Source: provided S&P 500 dataset.")
)

finalize(gt, "table.png")
