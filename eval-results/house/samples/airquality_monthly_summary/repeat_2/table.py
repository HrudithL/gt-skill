import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, heatmap, humanize_labels

# Load the air quality data
df = pd.read_csv("airquality.csv")

# Create a mapping for month numbers to names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

# Group by month and calculate averages
monthly_data = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to month names
monthly_data["Month"] = monthly_data["Month"].map(month_names)

# Rename columns for display
monthly_data = monthly_data.rename(columns={
    "Month": "month",
    "Temp": "temp",
    "Wind": "wind",
    "Ozone": "ozone"
})

# Create the GT table
gt = GT(monthly_data, rowname_col="month")
gt = gt.tab_header(
    title="Monthly Air Quality Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month")
)

# Format numeric columns
gt = gt.fmt_number(columns=["temp", "wind", "ozone"], decimals=1)

# Apply humanized labels
gt = humanize_labels(
    gt,
    monthly_data,
    overrides={
        "temp": "Avg Temperature (°F)",
        "wind": "Avg Wind Speed (mph)",
        "ozone": "Avg Ozone (ppb)"
    }
)

# Apply band with light navy tint
gt = band(gt, hue="navy")

# Apply one heatmap for the hero measure (temperature)
gt = heatmap(gt, "temp", kind="sequential", hue="neutral")

# Add hairlines, frame, and finalize
gt = hairlines(gt)
gt = frame(gt)

gt.tab_source_note(source_note="Source: Air Quality Dataset (May–September)")
finalize(gt, path="table.png")
