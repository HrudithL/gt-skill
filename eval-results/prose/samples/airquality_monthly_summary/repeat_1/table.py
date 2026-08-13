import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("./airquality.csv")

# Convert Month to month names for display
month_map = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month_Name"] = df["Month"].map(month_map)

# Group by month and calculate averages
monthly = df.groupby("Month_Name")[["Temp", "Wind", "Ozone"]].mean().reset_index()
monthly = monthly.rename(columns={"Month_Name": "Month"})

# Round to 1 decimal place
monthly["Temp"] = monthly["Temp"].round(1)
monthly["Wind"] = monthly["Wind"].round(1)
monthly["Ozone"] = monthly["Ozone"].round(1)

# Compute domains for data_color
ozone_cols = ["Ozone"]
ozone_lo = float(np.nanmin(monthly[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly[ozone_cols].to_numpy()))

temp_cols = ["Temp"]
temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))

gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1, use_seps=False)
    .data_color(
        columns="Temp",
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Ozone",
        palette="Reds",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    .cols_label(Temp="Temperature (°F)", Wind="Wind Speed (mph)", Ozone="Ozone (ppb)")
    .cols_width(cases={"Temp": "130px", "Wind": "130px", "Ozone": "130px"})
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average temperature, wind speed, and ozone levels"
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_source_note(source_note="Temperature shown in Fahrenheit, wind speed in miles per hour, and ozone in parts per billion (ppb).")
    .tab_source_note(source_note="Source: New York air quality data.")
)

gt.gtsave("table.png", expand=15)
