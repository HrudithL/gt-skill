import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("airquality.csv")

df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

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
monthly = monthly.rename(columns={"Month": "Month", "Temp": "Avg Temp (°F)", "Wind": "Avg Wind (mph)", "Ozone": "Avg Ozone (ppb)"})

lo_temp = float(np.nanmin(monthly[["Avg Temp (°F)"]].to_numpy()))
hi_temp = float(np.nanmax(monthly[["Avg Temp (°F)"]].to_numpy()))

gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], decimals=1, use_seps=True)
    .data_color(
        columns=["Avg Temp (°F)"],
        palette="Blues",
        domain=[lo_temp, hi_temp],
        truncate=False,
        na_color="#808080",
    )
    .tab_style(
        style=style.borders(sides="top", color="#BDBDBD", weight="1.5px"),
        locations=loc.body(rows=[]),
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
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
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels by Month"
    )
    .tab_source_note(source_note="Temperature is colored by magnitude to show seasonal variation.")
    .tab_source_note(source_note="Source: airquality.csv")
)

gt.gtsave("table.png", expand=15)
