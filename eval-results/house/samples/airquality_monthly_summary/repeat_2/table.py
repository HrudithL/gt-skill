import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, humanize_labels, heatmap

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Month name mapping
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# Calculate monthly averages
monthly_summary = df.groupby("Month").agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean",
}).reset_index()

# Map month numbers to names
monthly_summary["Month"] = monthly_summary["Month"].map(month_names)

# Round to 1 decimal place
monthly_summary = monthly_summary.round(1)

# Create GT table
gt = (
    GT(monthly_summary, rowname_col="Month")
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle=md("Average temperature, wind speed, and ozone levels by month"),
    )
    .fmt_number(columns=["Ozone", "Wind", "Temp"], decimals=1)
)

# Humanize column labels
gt = humanize_labels(
    gt,
    monthly_summary,
    overrides={"Ozone": "Ozone (ppb)", "Wind": "Wind Speed (mph)", "Temp": "Temperature (°F)"},
)

# Apply heatmap coloring to the numeric columns
# Ozone: sequential (Blues, neutral - higher values are worse for air quality)
gt = heatmap(gt, ["Ozone", "Wind", "Temp"], kind="sequential", hue="neutral")

# Apply striping
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue="navy")

# Apply heading band
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Apply row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png", zoom=2.0, expand=15)
