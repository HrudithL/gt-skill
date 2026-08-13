import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize

df = pd.read_csv("airquality.csv")

# Step 1: Clean and prepare data
# Convert to numeric, dropping NaN values per measure
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Group by month and compute averages
monthly = df.groupby("Month", as_index=False).agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean"
}).round(1)

# Map month numbers to names for the stub
month_names = {
    5: "May", 6: "June", 7: "July", 8: "August", 9: "September"
}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Reorder and select columns
monthly = monthly[["Month_Name", "Ozone", "Wind", "Temp"]]
monthly = monthly.rename(columns={"Month_Name": "Month"})

# Step 2: Organize columns with stub
gt = GT(monthly, rowname_col="Month")

# Step 3: Add color fills for Ozone (ordered magnitude) and Temperature
# Both are distinct physical measurements
ozone_cols = ["Ozone"]
temp_cols = ["Temp"]

# Ozone gradient (neutral magnitude → Blues)
oz_min = float(np.nanmin(monthly[ozone_cols].to_numpy()))
oz_max = float(np.nanmax(monthly[ozone_cols].to_numpy()))
gt = heatmap(gt, ozone_cols, kind="sequential", hue="neutral", domain=[oz_min, oz_max])

# Temperature gradient (neutral magnitude, distinct measure → Greens as secondary)
temp_min = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_max = float(np.nanmax(monthly[temp_cols].to_numpy()))
gt = heatmap(gt, temp_cols, kind="sequential", hue="positive", domain=[temp_min, temp_max])

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Small-color polish
# Format numbers
gt = (
    gt
    .fmt_number(columns=["Ozone", "Wind", "Temp"], decimals=1, use_seps=False)
    .sub_missing(columns=["Ozone", "Wind", "Temp"], missing_text="—")
)

# Row striping
gt = stripe(gt)

# Stub tint
gt = stub_tint(gt)

# Frame (boxed border)
gt = frame(gt)

# Compact layout
gt = gt.cols_width(cases={
    "Ozone": "100px",
    "Wind": "100px",
    "Temp": "100px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="Air Quality Measurements by Month",
        subtitle="Average Monthly Temperature, Wind Speed, and Ozone Levels"
    )
    .tab_source_note(source_note="Ozone measured in ppb; Temperature in °F; Wind speed in mph.")
    .tab_source_note(source_note="Source: airquality.csv")
)

# Step 7: Render
finalize(gt, "table.png")
