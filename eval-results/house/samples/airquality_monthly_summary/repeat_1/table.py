import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from house_table import (
    PALETTE, frame, hairlines, finalize, band, heatmap, humanize_labels
)

# Load and aggregate data
df = pd.read_csv("airquality.csv")

# Compute monthly averages
monthly_summary = df.groupby("Month").agg(
    Ozone=("Ozone", "mean"),
    Wind=("Wind", "mean"),
    Temperature=("Temp", "mean"),
).reset_index()

# Rename month to a human-readable format
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
monthly_summary["Month"] = monthly_summary["Month"].map(month_names)

# Create GT object with month as stub
gt = GT(monthly_summary, rowname_col="Month")

# Title and subtitle
gt = gt.tab_header(
    title="Air Quality Summary by Month",
    subtitle=md("Average temperature, wind speed, and ozone levels across months"),
)

# Rename stub column
gt = gt.tab_stubhead(label="Month")

# Format numeric columns
gt = gt.fmt_number(columns="Ozone", decimals=1)
gt = gt.fmt_number(columns="Wind", decimals=1)
gt = gt.fmt_number(columns="Temperature", decimals=1)

# Apply humanize_labels
gt = humanize_labels(gt, monthly_summary)

# Heatmaps for the three measures
gt = heatmap(gt, "Ozone", kind="sequential", hue="warning")
gt = heatmap(gt, "Wind", kind="sequential", hue="neutral")
gt = heatmap(gt, "Temperature", kind="sequential", hue="positive")

# Apply heading band
gt = band(gt, hue="navy")

# Small-color polish
gt = gt.opt_row_striping().tab_options(
    row_striping_background_color=PALETTE["neutral"]["row_stripe"],
)

# Source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Ozone levels (ppb), wind speed (mph), and temperature (°F) represent monthly averages."
)
gt = gt.tab_source_note(
    source_note="Source: airquality.csv dataset."
)

# Hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Finalize and render
finalize(gt, path="table.png")
