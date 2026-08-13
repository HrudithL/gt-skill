import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

df = pd.read_csv("airquality.csv")

df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

agg_df = df.groupby("Month").agg({
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

agg_df["Month"] = agg_df["Month"].map(month_names)

cols_measure = ["Temp", "Wind", "Ozone"]

lo_temp = float(np.nanmin(agg_df[["Temp"]].to_numpy()))
hi_temp = float(np.nanmax(agg_df[["Temp"]].to_numpy()))

lo_ozone = float(np.nanmin(agg_df[["Ozone"]].to_numpy()))
hi_ozone = float(np.nanmax(agg_df[["Ozone"]].to_numpy()))

gt = (
    GT(agg_df, rowname_col="Month")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
    .cols_label(
        Temp="Temperature (°F)",
        Wind="Wind Speed (mph)",
        Ozone="Ozone (ppb)"
    )
    .data_color(
        columns=["Temp"],
        palette="Blues",
        domain=[lo_temp, hi_temp],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Ozone"],
        palette="Reds",
        domain=[lo_ozone, hi_ozone],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels (May–September 1973)"
    )
    .tab_options(
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
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
        row_striping_background_color="#F6F6F6",
    )
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .cols_width(cases={
        "Month": "100px",
        "Temp": "130px",
        "Wind": "140px",
        "Ozone": "130px"
    })
    .sub_missing(columns=["Temp", "Wind", "Ozone"], missing_text="—")
    .tab_source_note(source_note="Average values computed across all observations for each month.")
    .tab_source_note(source_note="Source: airquality.csv")
)

gt.gtsave("table.png", expand=15)
