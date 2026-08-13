import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Read and clean data
df = pd.read_csv("airquality.csv")

# Coerce numeric columns and compute monthly averages
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Group by Month and calculate averages
monthly = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Map month numbers to names for better readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Prepare for display with Month_Name as the stub
monthly_display = monthly[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
monthly_display.columns = ["Month", "Temperature", "Wind Speed", "Ozone"]

# Step 2: Organize columns — Month is the stub
gt = GT(monthly_display, rowname_col="Month")

# Step 3: Add heatmaps for Temperature and Ozone (two distinct environmental measures)
gt = (
    gt
    # Format all numeric columns
    .fmt_number(columns=["Temperature", "Wind Speed", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temperature", "Wind Speed", "Ozone"], missing_text="—")
)

# Heatmap for Temperature (neutral magnitude → Blues)
gt = heatmap(gt, "Temperature", kind="sequential", hue="neutral")

# Heatmap for Ozone (neutral magnitude → Blues, secondary, so use Greens per fallback ladder)
gt = heatmap(gt, "Ozone", kind="sequential", hue="warning")

# Step 4: Apply heading band (navy, bold, white text)
gt = band(gt)

# Step 5: Small-color polish
# (a) Cell borders — hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (c) Row striping
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt)

# Frame (all four sides)
gt = frame(gt)

# Compact layout — column widths and padding
gt = gt.cols_width(cases={"Month": "120px", "Temperature": "130px", "Wind Speed": "120px", "Ozone": "110px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = (
    gt
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .tab_source_note(source_note="Monthly averages computed from daily observations; Temperature in °F, Wind Speed in mph, Ozone in ppb.")
    .tab_source_note(source_note="Source: airquality.csv")
)

# Step 7: Render
finalize(gt)
