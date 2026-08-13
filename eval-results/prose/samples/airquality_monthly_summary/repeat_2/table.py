import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Read and clean the data
df = pd.read_csv("airquality.csv")

# Convert to correct dtypes
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Aggregate by month
monthly = df.groupby("Month").agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean"
}).reset_index()

# Create month names for the stub
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Step 2: Organize columns
summary = monthly[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
summary.columns = ["Month", "Temperature", "Wind_Speed", "Ozone"]

# Step 3: Prepare color data
# Both Temperature and Ozone are distinct dimensions of air quality
temp_lo = float(np.nanmin(summary["Temperature"].to_numpy()))
temp_hi = float(np.nanmax(summary["Temperature"].to_numpy()))
ozone_lo = float(np.nanmin(summary["Ozone"].to_numpy()))
ozone_hi = float(np.nanmax(summary["Ozone"].to_numpy()))

# Step 4 & 5 & 6: Build the table with all formatting
gt = (
    GT(summary, rowname_col="Month")
    # Formatting
    .fmt_number(columns=["Temperature"], decimals=1, use_seps=True)
    .fmt_number(columns=["Wind_Speed"], decimals=1, use_seps=True)
    .fmt_number(columns=["Ozone"], decimals=1, use_seps=True)
    .sub_missing(columns=["Temperature", "Wind_Speed", "Ozone"], missing_text="—")
    # Column labels
    .cols_label(
        Temperature="Temperature (°F)",
        Wind_Speed="Wind Speed (mph)",
        Ozone="Ozone (ppb)"
    )
    # Big Color: Temperature and Ozone both colored as distinct dimensions
    .data_color(
        columns=["Temperature"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080"
    )
    .data_color(
        columns=["Ozone"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080"
    )
    # Heading band
    .tab_header(
        title="Air Quality by Month",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    # Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Heading band style (Step 4 constant)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # Frame border
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
    )
    # Compact layout padding
    .cols_width(cases={
        "Month": "120px",
        "Temperature": "150px",
        "Wind_Speed": "150px",
        "Ozone": "140px"
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles & annotations (Step 6)
    .tab_source_note(source_note="Temperature and Ozone show distinct dimensions of air quality patterns; Wind Speed shown for context.")
    .tab_source_note(source_note="Source: airquality.csv — daily measurements from New York, May–September 1973.")
)

gt.gtsave("table.png", expand=15)
