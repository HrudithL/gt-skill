import pandas as pd
from great_tables import GT, loc, style, md
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, humanize_labels, heatmap

# Read the air quality dataset
df = pd.read_csv("airquality.csv")

# Map month numbers to month names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month_Name"] = df["Month"].map(month_names)

# Group by month and calculate averages
monthly_summary = df.groupby(["Month", "Month_Name"]).agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Round to 1 decimal place
monthly_summary["Temp"] = monthly_summary["Temp"].round(1)
monthly_summary["Wind"] = monthly_summary["Wind"].round(1)
monthly_summary["Ozone"] = monthly_summary["Ozone"].round(1)

# Drop the numeric month column, keep only Month_Name as stub
display_df = monthly_summary[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
display_df = display_df.rename(columns={
    "Month_Name": "month",
    "Temp": "temperature",
    "Wind": "wind_speed",
    "Ozone": "ozone"
})

# Build the table
gt = GT(display_df, rowname_col="month")
gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month")
)

# Format columns
gt = gt.fmt_number(columns=["temperature", "wind_speed", "ozone"], decimals=1)

# Humanize labels
gt = humanize_labels(gt, display_df)

# Apply heatmaps: temperature (sequential) and ozone (warning/sequential)
gt = heatmap(gt, "temperature", kind="sequential", hue="neutral")
gt = heatmap(gt, "ozone", kind="sequential", hue="warning")

# Heading band with light tint
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Stub tint to match the band hue (navy)
gt = stub_tint(gt, hue="navy")

# Add source note
gt = gt.tab_source_note(source_note="Source: air quality dataset.")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png", zoom=2.0, expand=15)
