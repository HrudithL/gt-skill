import sys
import pandas as pd
import numpy as np
from great_tables import GT, style, loc

sys.path.insert(0, ".claude/skills/great-tables-ci/scripts")
from gt_consistency import band, frame, finalize

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

df_monthly = []
for year_month, month_data in df.groupby(df["date"].dt.to_period("M")):
    month_data = month_data.sort_values("date")

    opening = month_data.iloc[0]["open"]
    closing = month_data.iloc[-1]["close"]
    pct_change = ((closing - opening) / opening) * 100

    avg_volume = month_data["volume"].mean()

    intraday_gains = month_data["high"] - month_data["low"]
    best_gain = intraday_gains.max()

    daily_changes = month_data["close"].diff()
    worst_loss = daily_changes.min()

    df_monthly.append({
        "month": str(year_month),
        "opening": opening,
        "closing": closing,
        "pct_change": pct_change,
        "avg_volume": avg_volume,
        "best_day_gain": best_gain,
        "worst_day_loss": worst_loss,
    })

df_month = pd.DataFrame(df_monthly)
df_month["month"] = pd.to_datetime(df_month["month"])
df_month = df_month[
    (df_month["month"].dt.year >= 2010) & (df_month["month"].dt.year <= 2015)
].copy()

df_month["month_label"] = df_month["month"].dt.strftime("%b %Y")
df_month = df_month.drop("month", axis=1)
df_month = df_month[["month_label", "opening", "closing", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"]]

lo_pct = float(np.nanmin(df_month[["pct_change"]].to_numpy()))
hi_pct = float(np.nanmax(df_month[["pct_change"]].to_numpy()))

lo_vol = float(np.nanmin(df_month[["avg_volume"]].to_numpy()))
hi_vol = float(np.nanmax(df_month[["avg_volume"]].to_numpy()))

lo_gain = float(np.nanmin(df_month[["best_day_gain"]].to_numpy()))
hi_gain = float(np.nanmax(df_month[["best_day_gain"]].to_numpy()))

lo_loss = float(np.nanmin(df_month[["worst_day_loss"]].to_numpy()))
hi_loss = float(np.nanmax(df_month[["worst_day_loss"]].to_numpy()))

gt = (
    GT(df_month, rowname_col="month_label")
    .tab_stubhead(label="Month")
    .fmt_number(columns=["opening", "closing"], decimals=2, use_seps=True)
    .fmt_percent(columns=["pct_change"], decimals=2, force_sign=True, scale_values=False)
    .fmt_number(columns=["avg_volume"], decimals=0, use_seps=True)
    .fmt_number(columns=["best_day_gain", "worst_day_loss"], decimals=2)
    .tab_spanner(label="Price", columns=["opening", "closing"])
    .tab_spanner(label="Performance", columns=["pct_change", "avg_volume", "best_day_gain", "worst_day_loss"])
    .cols_label(
        opening="Open",
        closing="Close",
        pct_change="% Change",
        avg_volume="Avg Daily Vol",
        best_day_gain="Best Day Gain",
        worst_day_loss="Worst Day Loss",
    )
    .cols_width(cases={
        "month_label": "110px",
        "opening": "100px",
        "closing": "100px",
        "pct_change": "100px",
        "avg_volume": "120px",
        "best_day_gain": "130px",
        "worst_day_loss": "130px",
    })
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="closing"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="closing"),
    )
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[lo_pct, hi_pct],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[lo_vol, hi_vol],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[lo_gain, hi_gain],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["worst_day_loss"],
        palette="Reds",
        domain=[lo_loss, hi_loss],
        truncate=False,
        na_color="#808080",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
)

gt = band(gt)
gt = frame(gt)

gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010–2015",
)

gt = gt.tab_source_note(
    "Best-day gain is the largest single day intraday high-to-low range. Worst-day loss is the largest single-day close-to-close decline."
)

gt = gt.tab_source_note(
    "Data source: Historical S&P 500 daily close data"
)

finalize(gt)
