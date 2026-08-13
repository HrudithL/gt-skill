import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and understand the data
df = pd.read_csv("./airquality.csv")

# Verify we have the required columns
required_cols = ["Ozone", "Wind", "Temp", "Month"]
if not all(col in df.columns for col in required_cols):
    raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")

# Step 1 (continued): Data cleaning
# Ensure numeric columns are properly typed
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

# Step 2: Organize columns - aggregate by month
# Group by month and compute averages
monthly_data = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Create month names for the stub
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_data["Month_Name"] = monthly_data["Month"].map(month_names)

# Organize columns: Month_Name (stub), then the measures
monthly_data = monthly_data[["Month_Name", "Temp", "Wind", "Ozone"]]

# Step 3: Determine Big Color
# Three measures requested: temperature, wind speed, ozone
# All three are ordered magnitudes with ≥5 observations
# Prompt emphasizes: temperature, wind speed, ozone (in that order from the request)
# Temperature and Ozone are distinct physical measurements, so both color
# Wind speed has no narrative role per the expected output, so keep plain

# Compute domains for colored measures (temperature and ozone)
temp_lo = float(np.nanmin(monthly_data["Temp"].to_numpy()))
temp_hi = float(np.nanmax(monthly_data["Temp"].to_numpy()))
ozone_lo = float(np.nanmin(monthly_data["Ozone"].to_numpy()))
ozone_hi = float(np.nanmax(monthly_data["Ozone"].to_numpy()))

# Step 4 & 5: Build the GT table with heading band and polish
gt = (
    GT(monthly_data, rowname_col="Month_Name")
    # Rename column labels for clarity (Step 2/6 naming)
    .cols_label(
        Temp="Temperature (°F)",
        Wind="Wind Speed (mph)",
        Ozone="Ozone (ppb)"
    )
    # Format numbers
    .fmt_number(columns=["Temp"], decimals=1)
    .fmt_number(columns=["Wind"], decimals=1)
    .fmt_number(columns=["Ozone"], decimals=1)
    # Step 3: Big Color - apply data_color for Temperature and Ozone
    .data_color(
        columns=["Temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Ozone"],
        palette="Blues",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - dark navy background (white text from auto-contrast)
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average temperature, wind speed, and ozone levels"
    )
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color - cell borders, striping, stub tint
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 6: Titles & annotations - footer notes (two separate calls for ≥5 rows)
    .tab_source_note(
        "Temperature and ozone levels are heatmapped to show relative magnitudes across months. "
        "Wind speed displayed for context."
    )
    .tab_source_note(
        "Source: R datasets::airquality (monthly aggregations of daily observations)"
    )
)

# Step 7: Render and verify
gt.gtsave("table.png")
print("Table rendered successfully to table.png")
