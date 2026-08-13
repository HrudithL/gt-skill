import sys
sys.path.insert(0, '.claude/skills/great-tables-ci/scripts')

import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint, hairlines

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Convert numeric columns and ensure proper dtype
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = df["Month"].astype(int)
df["Day"] = df["Day"].astype(int)

# Step 2: Create monthly aggregations
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to month names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month"] = monthly["Month"].map(month_names)

# Round to 1 decimal place
monthly["Temp"] = monthly["Temp"].round(1)
monthly["Wind"] = monthly["Wind"].round(1)
monthly["Ozone"] = monthly["Ozone"].round(1)

# Rename columns for display
monthly = monthly.rename(columns={
    "Month": "Month",
    "Temp": "Avg Temperature (°F)",
    "Wind": "Avg Wind Speed (mph)",
    "Ozone": "Avg Ozone (ppb)"
})

# Step 3: Build the table - starting with GT constructor and headers
gt = GT(monthly, rowname_col="Month")
gt = gt.tab_header(
    title="Monthly Air Quality Summary",
    subtitle="Average temperature, wind speed, and ozone levels"
)

# Step 3: Color the measures (temperature and ozone as distinct dimensions)
# Temperature: neutral magnitude → Blues
gt = heatmap(gt, columns="Avg Temperature (°F)", kind="sequential", hue="neutral")
# Ozone: environmental/growth → Greens (distinct from temperature)
gt = heatmap(gt, columns="Avg Ozone (ppb)", kind="sequential", hue="positive")
# Wind speed stays plain (carries no narrative role in this request)

# Step 4: Apply heading band (fixed branding)
gt = band(gt)

# Step 5: Apply small color checklist in order
# (a) Cell hairlines
gt = hairlines(gt)
# (c) Row striping
gt = stripe(gt)
# (d) Stub tint
gt = stub_tint(gt)

# Format numbers
gt = (gt
    .fmt_number(
        columns="Avg Temperature (°F)",
        decimals=1
    )
    .fmt_number(
        columns="Avg Wind Speed (mph)",
        decimals=1
    )
    .fmt_number(
        columns="Avg Ozone (ppb)",
        decimals=1
    )
    # Column widths
    .cols_width(cases={
        "Month": "120px",
        "Avg Temperature (°F)": "150px",
        "Avg Wind Speed (mph)": "150px",
        "Avg Ozone (ppb)": "130px",
    })
    # Compact layout padding
    .tab_options(
        heading_padding="8px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="6px",
        data_row_padding_horizontal="8px",
        source_notes_padding="8px",
    )
    # Step 6: Add footer (two-call convention for ≥5 rows)
    .tab_source_note("Ozone and temperature are colored to show relative levels across months. Wind speed is shown for context.")
    .tab_source_note("Data: Monthly averages of daily observations from the New York air quality dataset.")
)

# Step 7: Apply frame and finalize
gt = frame(gt)
finalize(gt)
