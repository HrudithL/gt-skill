import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Load and clean data
df = pd.read_csv("./airquality.csv")

# Create monthly summary
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month"] = monthly["Month"].map(month_names)
monthly = monthly.rename(columns={"Month": "Month"})

# Compute data ranges for color domain
cols_color = ["Ozone", "Temp"]
lo_o = float(np.nanmin(monthly["Ozone"]))
hi_o = float(np.nanmax(monthly["Ozone"]))
lo_t = float(np.nanmin(monthly["Temp"]))
hi_t = float(np.nanmax(monthly["Temp"]))

# Build table
gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
    .data_color(
        columns="Temp",
        palette="Blues",
        domain=[lo_t, hi_t],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Ozone",
        palette="Greens",
        domain=[lo_o, hi_o],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average temperature, wind speed, and ozone levels by month"
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
    .sub_missing(columns=["Temp", "Wind", "Ozone"], missing_text="—")
    .tab_source_note(source_note="Average values computed across all days in each month.")
    .tab_source_note(source_note="Source: New York air quality dataset.")
)

gt.gtsave("table.png", expand=15)
