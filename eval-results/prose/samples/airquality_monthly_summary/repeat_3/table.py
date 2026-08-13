import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean the data
df = pd.read_csv("airquality.csv")

# Calculate monthly averages
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Prepare final dataframe with Month as stub
df_display = monthly[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
df_display.columns = ["Month", "Avg_Temp", "Avg_Wind", "Avg_Ozone"]

# Step 3: Big Color — compute domains for color fills
# Temperature (primary neutral measure) → Blues
temp_lo = float(np.nanmin(df_display[["Avg_Temp"]].to_numpy()))
temp_hi = float(np.nanmax(df_display[["Avg_Temp"]].to_numpy()))

# Ozone (secondary neutral measure) → Greens (fallback neutral ladder)
ozone_lo = float(np.nanmin(df_display[["Avg_Ozone"]].to_numpy()))
ozone_hi = float(np.nanmax(df_display[["Avg_Ozone"]].to_numpy()))

# Step 2: Build the table
gt = (
    GT(df_display, rowname_col="Month")
    # Step 2: Column organization
    .cols_label(
        Avg_Temp="Avg. Temperature (°F)",
        Avg_Wind="Avg. Wind Speed (mph)",
        Avg_Ozone="Avg. Ozone (ppb)"
    )
    .cols_width(cases={
        "Month": "120px",
        "Avg_Temp": "140px",
        "Avg_Wind": "140px",
        "Avg_Ozone": "140px"
    })
    # Step 3: Big Color — gradient fills for temperature and ozone
    .fmt_number(columns=["Avg_Temp", "Avg_Wind", "Avg_Ozone"], decimals=1)
    .data_color(
        columns=["Avg_Temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Avg_Ozone"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — dark navy with white text
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels (May–September)"
    )
    .tab_options(
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels()
    )
    # Step 5: Small-color polish
    .tab_options(
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
    .opt_row_striping(row_striping=True)
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    .sub_missing(columns=["Avg_Temp", "Avg_Wind", "Avg_Ozone"], missing_text="—")
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & annotations
    .tab_source_note(
        source_note="Average Ozone and Temperature are both measured across the five-month period. Wind speed is reported as context."
    )
    .tab_source_note(
        source_note="Source: airquality.csv"
    )
)

# Render
gt.gtsave("table.png", expand=15)
print("✓ table.png created successfully")
