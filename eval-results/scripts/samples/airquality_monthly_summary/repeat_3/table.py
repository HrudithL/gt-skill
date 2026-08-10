import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe

df = pd.read_csv("airquality.csv")

# Clean the data: coerce numeric columns
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Aggregate by month: average temperature, wind speed, and ozone
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).reset_index()

# Create month labels for readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]
monthly = monthly.rename(columns={
    "Month_Name": "Month",
    "Temp": "Temperature (°F)",
    "Wind": "Wind Speed (mph)",
    "Ozone": "Ozone (ppb)"
})

# Create the table
gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(
        columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"],
        decimals=1
    )
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .tab_source_note("Average values computed from daily measurements")
    .tab_source_note("Source: New York air quality dataset (May–September)")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# Apply heading band (light, with forest hue since we have Big Color)
gt = band(gt, shade="light", hue="forest")

# Color the Ozone column using heatmap helper (ordered magnitude)
gt = heatmap(gt, ["Ozone (ppb)"], kind="sequential", hue="warning")

# Bold the Temperature column (secondary measure)
gt = gt.tab_style(
    style=style.text(weight="bold"),
    locations=loc.body(columns=["Temperature (°F)"])
)

# Apply striping
gt = stripe(gt)

# Apply frame
gt = frame(gt)

# Render and save
finalize(gt, "table.png")
