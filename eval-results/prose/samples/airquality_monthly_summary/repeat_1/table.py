import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

df = pd.read_csv("airquality.csv")

monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

cols = ["Ozone"]
lo = float(np.nanmin(monthly[cols].to_numpy()))
hi = float(np.nanmax(monthly[cols].to_numpy()))

gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["Temp", "Wind"]),
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
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .cols_label(
        Month="Month",
        Temp="Avg Temperature (°F)",
        Wind="Avg Wind Speed (mph)",
        Ozone="Avg Ozone (ppb)"
    )
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .tab_source_note(source_note="Ozone levels are color-coded to highlight seasonal variation; higher values indicate greater ozone concentrations.")
    .tab_source_note(source_note="Source: New York air quality data (May–September)")
)

gt.gtsave("table.png", expand=15)
