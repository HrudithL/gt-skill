import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe

# Step 1: Read and clean the data
df = pd.read_csv("airquality.csv")

# Coerce numeric columns to float, handling missing values
for col in ["Ozone", "Solar_R", "Wind", "Temp"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Group by Month and calculate mean values
monthly_stats = (
    df.groupby("Month")[["Temp", "Wind", "Ozone"]]
    .mean()
    .round(1)
    .reset_index()
)

# Create month labels (May through September)
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly_stats["Month_Label"] = monthly_stats["Month"].map(month_names)

# Rename columns for display
display_df = monthly_stats[["Month_Label", "Temp", "Wind", "Ozone"]].copy()
display_df.columns = ["Month", "Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"]

# Step 2: Create GT table with Month as stub
gt = GT(display_df, rowname_col="Month")

# Step 3: Apply gradient coloring to all three measures (sequential)
# All three are neutral magnitude measures
gt = heatmap(gt, ["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"],
             kind="sequential", hue="neutral")

# Step 4: Apply heading band
gt = band(gt, shade="light", hue="navy")

# Step 5: Small-color polish
gt = frame(gt)
gt = stripe(gt)

# Format the numbers
gt = gt.fmt_number(columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"],
                   decimals=1)

# Add titles and annotations
gt = gt.tab_header(
    title="Monthly Air Quality Statistics",
    subtitle="Average Temperature, Wind Speed, and Ozone Levels (May–September)"
)

gt = gt.tab_source_note("Data source: Air Quality Dataset")

finalize(gt, "table.png")
