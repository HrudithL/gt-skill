import pandas as pd
import numpy as np
from great_tables import GT, loc, style

df = pd.read_csv("airquality.csv")

# Aggregate by month: mean of Ozone, Wind, and Temp
monthly = (
    df.groupby("Month")
    .agg(
        Temp=("Temp", "mean"),
        Wind=("Wind", "mean"),
        Ozone=("Ozone", "mean"),
    )
    .reset_index()
)

# Create month names for readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Compute domains for colors
temp_lo = float(np.nanmin(monthly["Temp"].to_numpy()))
temp_hi = float(np.nanmax(monthly["Temp"].to_numpy()))
ozone_lo = float(np.nanmin(monthly["Ozone"].to_numpy()))
ozone_hi = float(np.nanmax(monthly["Ozone"].to_numpy()))

gt = (
    GT(monthly, rowname_col="Month_Name")
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average temperature, wind speed, and ozone levels by month",
    )
    .cols_label(Temp="Temperature (°F)", Wind="Wind Speed (mph)", Ozone="Ozone (ppb)")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
    # Color temperature and ozone as the main measures of interest
    .data_color(
        columns=["Temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .data_color(
        columns=["Ozone"],
        palette="Oranges",
        domain=[ozone_lo, ozone_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Heading band — fixed branding navy, bold labels, white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
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
    .cols_width(
        cases={
            "Month_Name": "100px",
            "Temp": "110px",
            "Wind": "110px",
            "Ozone": "110px",
        }
    )
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .cols_align(align="right", columns=["Temp", "Wind", "Ozone"])
    .tab_source_note(
        source_note="Data represents mean values of daily measurements for each month."
    )
    .tab_source_note(
        source_note="Source: New York air quality dataset (May–September 1973)."
    )
)

gt.gtsave("table.png", zoom=2.0, expand=15)
