import pandas as pd
import numpy as np
from great_tables import GT, loc, style

df = pd.read_csv("./sp500.csv", parse_dates=["date"]).sort_values("date")

df_2010_2015 = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)].copy()

df_2010_2015["year_month"] = df_2010_2015["date"].dt.to_period("M")

monthly = df_2010_2015.groupby("year_month").agg(
    open=("open", "first"),
    close=("close", "last"),
    high=("high", "max"),
    low=("low", "min"),
    volume=("volume", "mean"),
    daily_change=("close", lambda x: x.diff().abs().max()),
).reset_index()

monthly["pct_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

monthly["month_label"] = monthly["year_month"].dt.strftime("%b %Y")

monthly = monthly[["month_label", "open", "close", "pct_change", "volume", "high", "low", "daily_change"]].reset_index(drop=True)

highest_gain = monthly["daily_change"].max()
monthly["highest_gain"] = monthly["high"] - monthly["low"]

lowest_loss = -monthly["daily_change"].min()
monthly["lowest_loss"] = -monthly["daily_change"]

monthly = monthly[["month_label", "open", "close", "pct_change", "volume", "highest_gain", "lowest_loss"]].reset_index(drop=True)

cols = ["pct_change"]
lo = float(np.nanmin(monthly[cols].to_numpy()))
hi = float(np.nanmax(monthly[cols].to_numpy()))
M = max(abs(lo), abs(hi))

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening/closing prices, percent change, volume, and intraday range",
    )
    .tab_stubhead(label="Month")
    .cols_label(
        open="Open ($)",
        close="Close ($)",
        pct_change="% Change",
        volume="Avg Daily Volume",
        highest_gain="Highest Daily Gain ($)",
        lowest_loss="Lowest Daily Loss ($)",
    )
    .fmt_currency(columns=["open", "close", "highest_gain", "lowest_loss"], currency="USD", decimals=2, use_seps=True)
    .fmt_number(columns=["volume"], decimals=0, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True)
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        reverse=False,
        domain=[-M, M],
        truncate=False,
    )
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
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
        row_striping_background_color="#F6F6F6",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .cols_align(align="right", columns=["open", "close", "pct_change", "volume", "highest_gain", "lowest_loss"])
    .cols_align(align="left", columns=["month_label"])
    .tab_source_note(source_note="Percent change is calculated as (Close − Open) / Open. Highest daily gain is the max intraday high minus low within each month. Lowest daily loss is the negated max daily change within each month.")
    .tab_source_note(source_note="Source: S&P 500 daily price data, 2010–2015.")
)

gt.gtsave("table.png", expand=15)
