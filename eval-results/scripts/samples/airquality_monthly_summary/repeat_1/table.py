import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# STEP 1: Understand and clean the data
df = pd.read_csv("airquality.csv")

# Ensure numeric columns are properly typed
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = df["Month"].astype(int)

# Compute monthly averages
monthly_avg = (
    df.groupby("Month")[["Temp", "Wind", "Ozone"]]
    .mean()
    .reset_index()
    .round(2)
)

# Create month name mapping
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly_avg["Month_Name"] = monthly_avg["Month"].map(month_names)

# Organize final dataframe: Month Name as stub, then the three measures
display_df = monthly_avg[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
display_df.columns = ["Month", "Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"]

# STEP 2: Organize columns - Month as stub
# STEP 3: Determine Big Color - 3 measures qualify (≥5 rows), cap at 2
# Priority: Temperature (mentioned first), Ozone (pollutant measure), Wind (secondary)
# Color Temperature (neutral magnitude → Blues) and Ozone (magnitude → Greens = "more is worse")

# STEP 4, 5, 3: Build the table with coloring
gt = GT(display_df, rowname_col="Month")

# Format numeric columns to 1 decimal place
gt = gt.fmt_number(
    columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"],
    decimals=1,
    use_seps=False
)

# Apply sub_missing for NA cells
gt = gt.sub_missing(columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"], missing_text="—")

# STEP 3: Apply Big Color - heatmap for the two colored measures
# Temperature (neutral magnitude → Blues), Ozone (warning/risk → Reds)
gt = heatmap(gt, "Temperature (°F)", kind="sequential", hue="neutral")
gt = heatmap(gt, "Ozone (ppb)", kind="sequential", hue="warning")

# Wind Speed stays uncolored (third measure, outside the 2-color ceiling)

# STEP 4: Apply heading band - light band since we have Big Color
gt = band(gt, shade="light", hue="navy")

# STEP 5: Small Color polish - apply checklist items
# (a) Cell borders - handled by defaults
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
)

# (c) Row striping - we have 5 rows, and body is not fully filled by Big Color
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt, hue="navy")

# Frame (global constant)
gt = frame(gt)

# STEP 6: Titles & Annotations
gt = (
    gt
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .tab_source_note(
        md("Data: New York Air Quality Measurements (May–September 1973)")
    )
)

# STEP 7: Render
finalize(gt, "table.png")
