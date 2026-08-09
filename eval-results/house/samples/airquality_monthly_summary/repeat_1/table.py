import pandas as pd
from great_tables import GT, loc, style
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Map month numbers to names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

# Compute monthly averages
monthly_stats = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()
monthly_stats["Month"] = monthly_stats["Month"].map(month_names)

# Rename columns for display
monthly_stats = monthly_stats.rename(columns={
    "Month": "month",
    "Temp": "avg_temperature",
    "Wind": "avg_wind_speed",
    "Ozone": "avg_ozone"
})

# Create the GT table with month as stub
gt = GT(monthly_stats, rowname_col="month")

# Add title and subtitle
gt = gt.tab_header(
    title="Air Quality Summary by Month",
    subtitle="Average temperature, wind speed, and ozone levels"
)

# Humanize column labels
gt = gt.cols_label(
    avg_temperature="Avg Temperature (°F)",
    avg_wind_speed="Avg Wind Speed (mph)",
    avg_ozone="Avg Ozone (ppb)"
)

# Format columns
gt = gt.fmt_number(columns=["avg_temperature", "avg_wind_speed"], decimals=1)
gt = gt.fmt_number(columns=["avg_ozone"], decimals=1)

# Apply house styling
gt = band(gt, shade="light", hue="forest")
gt = stub_tint(gt, hue="forest")

# Color the two main measures with sequential heatmaps
# Temperature: Blues (neutral magnitude)
gt = heatmap(gt, "avg_temperature", kind="sequential", hue="neutral")
# Wind speed: Greens (positive/growth)
gt = heatmap(gt, "avg_wind_speed", kind="sequential", hue="positive")

# Add row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"]
)

# Apply frame border
gt = frame(gt)

# Add source note
gt = gt.tab_source_note("Source: airquality dataset")

# Finalize and save
finalize(gt, path="table.png", zoom=2.0, expand=15)
