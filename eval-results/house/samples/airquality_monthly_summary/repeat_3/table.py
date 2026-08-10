import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stub_tint, heatmap,
    humanize_labels
)

# Load the data
df = pd.read_csv("airquality.csv")

# Calculate monthly averages
monthly_avg = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Create month names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly_avg["Month"] = monthly_avg["Month"].map(month_names)

# Round to 1 decimal place for display
monthly_avg["Temp"] = monthly_avg["Temp"].round(1)
monthly_avg["Wind"] = monthly_avg["Wind"].round(1)
monthly_avg["Ozone"] = monthly_avg["Ozone"].round(1)

# Create the GT table
gt = (
    GT(monthly_avg, rowname_col="Month")
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle=md("Average temperature, wind speed, and ozone levels by month")
    )
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
)

gt = humanize_labels(
    gt,
    monthly_avg,
    overrides={"Temp": "Temperature (°F)", "Wind": "Wind Speed (mph)", "Ozone": "Ozone (ppb)"}
)

# Apply the single heatmap to Ozone (the main air quality measure)
gt = heatmap(gt, "Ozone", kind="sequential", hue="warning")

# Apply heading band with forest hue (environment/nature theme)
gt = band(gt, hue="forest")

# Apply stub tint matching the band
gt = stub_tint(gt, hue="forest")

# Add hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided air quality dataset.")

# Finalize and render
finalize(gt)
