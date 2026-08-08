import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc

df = pd.read_csv("airquality.csv")

# Map numeric Month codes to human-readable month names
month_name = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# Aggregate by month: average temperature, wind speed, and ozone
monthly = df.groupby("Month").agg(
    temp_mean=("Temp", "mean"),
    wind_mean=("Wind", "mean"),
    ozone_mean=("Ozone", "mean"),
).reset_index()

monthly["month_label"] = monthly["Month"].map(month_name)
monthly = monthly[["month_label", "temp_mean", "wind_mean", "ozone_mean"]]

# Compute domains for the two colored measures (temperature and wind speed)
temp_cols = ["temp_mean"]
wind_cols = ["wind_mean"]
temp_min = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_max = float(np.nanmax(monthly[temp_cols].to_numpy()))
wind_min = float(np.nanmin(monthly[wind_cols].to_numpy()))
wind_max = float(np.nanmax(monthly[wind_cols].to_numpy()))

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="Air Quality — Summer 1973",
        subtitle="Monthly average temperature, wind speed, and ozone levels",
    )
    .cols_label(
        temp_mean=html("Temp (&deg;F)"),
        wind_mean="Wind (mph)",
        ozone_mean=html("Ozone (ppb)"),
    )
    .fmt_number(columns=["temp_mean", "wind_mean", "ozone_mean"], decimals=1)
    .data_color(
        columns="temp_mean",
        palette="Blues",
        domain=[temp_min, temp_max],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="wind_mean",
        palette="Greens",
        domain=[wind_min, wind_max],
        truncate=False,
        na_color="#808080",
    )
    .sub_missing(missing_text="—")
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_options(
        column_labels_background_color="#EAF0F6",
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
    )
    .tab_source_note(
        source_note="Source: New York State Department of Conservation, daily measurements May–September 1973."
    )
)

gt.gtsave("table.png", expand=15)
