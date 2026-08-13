import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import heatmap, band, stripe, stub_tint, frame, hairlines, finalize, PALETTE

# Load and clean data
df = pd.read_csv("airquality.csv")

# Coerce columns to numeric
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Aggregate by month
monthly = df.groupby("Month").agg(
    avg_temperature=("Temp", "mean"),
    avg_wind_speed=("Wind", "mean"),
    avg_ozone=("Ozone", "mean")
).reset_index()

# Create month names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly.drop(columns=["Month"])

# Round to 1 decimal
monthly["avg_temperature"] = monthly["avg_temperature"].round(1)
monthly["avg_wind_speed"] = monthly["avg_wind_speed"].round(1)
monthly["avg_ozone"] = monthly["avg_ozone"].round(1)

# Reorder columns
monthly = monthly[["Month_Name", "avg_temperature", "avg_wind_speed", "avg_ozone"]]

# Create the table
gt = (
    GT(monthly, rowname_col="Month_Name")
    .cols_label(
        avg_temperature="Avg Temp (°F)",
        avg_wind_speed="Avg Wind Speed (mph)",
        avg_ozone="Avg Ozone (ppb)"
    )
    .cols_width(cases={"Month_Name": "120px", "avg_temperature": "140px", "avg_wind_speed": "140px", "avg_ozone": "140px"})
    .fmt_number(columns=["avg_temperature", "avg_wind_speed", "avg_ozone"], decimals=1)
)

# Color temperature and ozone (two distinct physical measurements)
gt = heatmap(gt, ["avg_temperature"], kind="sequential", hue="neutral")
gt = heatmap(gt, ["avg_ozone"], kind="sequential", hue="positive")

# Apply branding and styling
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = hairlines(gt)

# Add padding
gt = gt.tab_options(
    heading_padding="12px",
    column_labels_padding="8px",
    column_labels_padding_horizontal="8px",
    data_row_padding="6px",
    data_row_padding_horizontal="8px",
    source_notes_padding="8px"
)

# Apply frame and titles
gt = (
    gt
    .tab_header(
        title="Air Quality: Monthly Summary (May–September 1973)",
        subtitle="Average temperature, wind speed, and ozone levels by month"
    )
    .tab_source_note("Measurements aggregated from daily observations in New York City area")
)

gt = frame(gt)
finalize(gt)
