import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Coerce columns to correct types
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

# Create month names for display
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month_Name"] = df["Month"].map(month_names)

# Group by month and calculate averages
agg_df = df.groupby("Month_Name")[["Temp", "Wind", "Ozone"]].mean().round(1).reset_index()

# Step 2: Organize columns
# Stub is Month_Name (row identifier)
agg_df = agg_df.rename(columns={"Month_Name": "Month"})

# Step 3: Big Color - color 2 measures (Temp and Wind, both ordered magnitudes)
# Temp is primary (temperature measurement), Wind is secondary
lo_temp = float(np.nanmin(agg_df[["Temp"]].to_numpy()))
hi_temp = float(np.nanmax(agg_df[["Temp"]].to_numpy()))

lo_wind = float(np.nanmin(agg_df[["Wind"]].to_numpy()))
hi_wind = float(np.nanmax(agg_df[["Wind"]].to_numpy()))

# Step 4: Build the table with formatting
gt = (
    GT(agg_df, rowname_col="Month")
    # Step 3: Big Color - heatmaps for the ordered measures
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1, use_seps=True)
)

# Apply heatmaps using the consistency helper
gt = heatmap(gt, ["Temp"], kind="sequential", hue="neutral", domain=[lo_temp, hi_temp])
gt = heatmap(gt, ["Wind"], kind="sequential", hue="positive", domain=[lo_wind, hi_wind])

# Step 4: Heading band - light band because Big Color is present
gt = band(gt, shade="light", hue="navy")

# Step 5: Small-Color polish
# (a) Cell borders - hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# (c) Row striping - apply since >= 5 rows and not fully color-filled
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt, hue="navy")

# Frame
gt = frame(gt)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="Air Quality Summary Statistics",
        subtitle="Average temperature, wind speed, and ozone levels by month"
    )
    .tab_source_note(
        source_note="Monthly averages computed from daily measurements across all observation days in each month."
    )
    .tab_source_note(
        source_note="Source: airquality.csv"
    )
)

# Step 7: Render
finalize(gt, "table.png")
