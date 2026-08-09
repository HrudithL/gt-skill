import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels
)

df = pd.read_csv("airquality.csv")

# Group by month and compute mean values for temperature, wind, and ozone
monthly_summary = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).round(2)

# Rename columns for clarity
monthly_summary = monthly_summary.rename(columns={
    "Temp": "temp",
    "Wind": "wind",
    "Ozone": "ozone"
})

# Map month numbers to month names
month_names = {
    5: "May", 6: "June", 7: "July", 8: "August", 9: "September"
}
monthly_summary.index = monthly_summary.index.map(month_names)
monthly_summary.index.name = "month"
monthly_summary = monthly_summary.reset_index()

gt = GT(monthly_summary)
gt = gt.tab_header(
    title="Air Quality Metrics by Month",
    subtitle=md("Average temperature, wind speed, and ozone levels for each month")
)
gt = humanize_labels(gt, monthly_summary)

# Format the numeric columns
gt = gt.fmt_number(columns=["temp", "wind", "ozone"], decimals=1)

# Apply heatmaps for the two most important measures
gt = heatmap(gt, "ozone", kind="sequential", hue="warning")
gt = heatmap(gt, "temp", kind="sequential", hue="neutral")

# Apply house format styling
gt = band(gt, hue="forest")
gt = stripe(gt)
gt = gt.tab_source_note(source_note="Source: provided dataset.")
gt = frame(gt)
finalize(gt, path="table.png")
