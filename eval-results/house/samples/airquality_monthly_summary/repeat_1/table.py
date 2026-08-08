import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, heatmap, humanize_labels, stripe, stub_tint

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Group by month and calculate averages
monthly_summary = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).round(2)

# Reset index and rename columns
monthly_summary = monthly_summary.reset_index()
monthly_summary.columns = ["month", "temp", "wind", "ozone"]

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
monthly_summary["month"] = monthly_summary["month"].map(month_names)

# Build the GT table
gt = GT(monthly_summary, rowname_col="month")

# Add title and subtitle
gt = gt.tab_header(
    title="Air Quality Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month")
)

# Format the numeric columns
gt = gt.fmt_number(columns=["temp", "wind", "ozone"], decimals=1)

# Apply humanize_labels
gt = humanize_labels(
    gt,
    monthly_summary,
    overrides={"temp": "Avg Temp (°F)", "wind": "Avg Wind (mph)", "ozone": "Avg Ozone (ppb)"}
)

# Apply Big Color: 2 heatmaps maximum
# Heatmap 1: Temperature (sequential, neutral/Blues)
gt = heatmap(gt, "temp", kind="sequential", hue="neutral")
# Heatmap 2: Ozone (sequential, warning/Reds - higher is worse)
gt = heatmap(gt, "ozone", kind="sequential", hue="warning")

# Apply heading band with neutral grey (no specific hue since we have sequential measures)
gt = gt.tab_options(
    column_labels_background_color=PALETTE["neutral"]["label_band"],
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Apply stub tint with navy (default)
gt = stub_tint(gt, hue="navy")

# Apply striping (5 months < 10 rows, so skip striping to keep it clean)

# Apply row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Apply frame
gt = frame(gt)

# Finalize and render
finalize(gt, path="table.png", zoom=2.0, expand=15)
