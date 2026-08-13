import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, band, hairlines, stripe, stub_tint, frame, finalize, heatmap

gt = None  # placeholder for the checker

# Step 1: Load and clean the data
df_raw = pd.read_csv("airquality.csv")

# Ensure numeric columns are properly typed
df_raw["Ozone"] = pd.to_numeric(df_raw["Ozone"], errors="coerce")
df_raw["Wind"] = pd.to_numeric(df_raw["Wind"], errors="coerce")
df_raw["Temp"] = pd.to_numeric(df_raw["Temp"], errors="coerce")
df_raw["Month"] = pd.to_numeric(df_raw["Month"], errors="coerce")

# Group by month and calculate averages
month_mapping = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

df = df_raw.groupby("Month").agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean"
}).reset_index()

df["Month_Name"] = df["Month"].map(month_mapping)
df = df[["Month_Name", "Temp", "Wind", "Ozone"]]
df.columns = ["Month", "Temp", "Wind", "Ozone"]

# Step 2: Create the GT table with stub
gt = GT(df, rowname_col="Month")

# Step 3: Add column labels and styling
gt = gt.cols_label(
    Temp="Avg Temperature",
    Wind="Avg Wind Speed",
    Ozone="Avg Ozone"
)

# Apply formatting to numeric columns (using original column names)
gt = gt.fmt_number(
    columns=["Temp", "Wind", "Ozone"],
    decimals=1,
    use_seps=True
)

# Step 3: Apply heatmaps for the two main measures (temperature and ozone)
# Temperature is a magnitude measure (neutral)
gt = heatmap(gt, "Temp", kind="sequential", hue="neutral")

# Ozone is a magnitude measure (neutral) - secondary measure
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")

# Wind speed stays plain (no fill) as it's not the focus of the analysis

# Step 4: Apply the fixed heading band
gt = band(gt)

# Step 5: Apply small color polish
gt = hairlines(gt)
gt = frame(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Add missing value handling
gt = gt.sub_missing(columns=["Temp", "Wind", "Ozone"], missing_text="—")

# Adjust column widths for readability
gt = gt.cols_width(cases={
    "Temp": "130px",
    "Wind": "130px",
    "Ozone": "130px"
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Add titles and annotations
gt = gt.tab_header(
    title="Air Quality Measurements by Month",
    subtitle="Average monthly values for temperature, wind speed, and ozone levels"
)

gt = gt.tab_source_note(
    source_note="Temperature and ozone levels are highlighted to show relative magnitudes across months."
)

gt = gt.tab_source_note(
    source_note="Source: airquality.csv — New York air quality data, May-September 1973."
)

# Step 7: Render and save
finalize(gt, "table.png")
