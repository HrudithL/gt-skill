import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, heatmap, stripe, stub_tint

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

monthly = df.groupby(df["date"].dt.to_period("M")).agg({
    "open": "first",
    "close": "last",
    "high": "max",
    "low": "min",
    "volume": "mean",
}).reset_index()

monthly["date"] = monthly["date"].dt.to_timestamp()
monthly = monthly.sort_values("date").reset_index(drop=True)

monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

daily_changes = df.copy()
daily_changes["intra_change"] = daily_changes["high"] - daily_changes["low"]
daily_changes["single_day_gain"] = daily_changes["high"] - daily_changes["open"]
daily_changes["single_day_loss"] = daily_changes["low"] - daily_changes["open"]
daily_changes["period"] = daily_changes["date"].dt.to_period("M")

period_gains = daily_changes.groupby("period")["single_day_gain"].max()
period_losses = daily_changes.groupby("period")["single_day_loss"].min()

monthly["highest_gain"] = monthly["date"].dt.to_period("M").map(period_gains)
monthly["max_loss"] = monthly["date"].dt.to_period("M").map(period_losses)

monthly = monthly[(monthly["date"] >= "2010-01-01") & (monthly["date"] <= "2015-12-31")].copy()
monthly = monthly.reset_index(drop=True)

monthly["year_month"] = monthly["date"].dt.strftime("%b %Y")

display_df = monthly[["year_month", "open", "close", "pct_change", "volume", "highest_gain", "max_loss"]].copy()
display_df.columns = ["month", "open", "close", "pct_change", "avg_volume", "highest_gain", "max_loss"]

gt = (
    GT(display_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance (2010–2015)",
        subtitle=md("Opening and closing prices, monthly return, average daily volume, and single-day extremes"),
    )
    .fmt_number(columns="open", decimals=2)
    .fmt_number(columns="close", decimals=2)
    .fmt_percent(columns="pct_change", decimals=2)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_number(columns="highest_gain", decimals=2)
    .fmt_number(columns="max_loss", decimals=2)
)

gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = gt.tab_source_note(source_note="Source: S&P 500 daily price data (2010–2015).")

gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
