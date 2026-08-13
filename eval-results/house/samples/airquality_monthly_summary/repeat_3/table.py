import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Load the air quality data
df = pd.read_csv("airquality.csv")

# Group by Month and compute monthly averages
monthly_stats = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).reset_index()

# Rename columns for display
monthly_stats.columns = ["Month", "temp", "wind", "ozone"]

# Map month numbers to month names for the stub
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_stats["month_name"] = monthly_stats["Month"].map(month_names)
monthly_stats = monthly_stats[["month_name", "temp", "wind", "ozone"]]
monthly_stats.columns = ["month", "temp", "wind", "ozone"]

# Build the GT table
gt = (
    GT(monthly_stats, rowname_col="month")
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle=md("Average temperature, wind speed, and ozone levels by month")
    )
    .tab_stubhead(label="Month")
)

# Format the numeric columns
gt = (
    gt.fmt_number(columns="temp", decimals=1)
    .fmt_number(columns="wind", decimals=2)
    .fmt_number(columns="ozone", decimals=2)
    .sub_missing(columns=["temp", "wind", "ozone"], missing_text="—")
)

# Apply humanized labels
gt = humanize_labels(gt, monthly_stats)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "month": "100px",
        "temp": "110px",
        "wind": "110px",
        "ozone": "110px",
    }
)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmaps to the three measures (all are sequential, positive magnitudes)
gt = heatmap(gt, "temp", kind="sequential", hue="positive")
gt = heatmap(gt, "wind", kind="sequential", hue="neutral")
gt = heatmap(gt, "ozone", kind="sequential", hue="warning")

# Apply branding and polish
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = gt.tab_source_note(
    source_note="Temperature in °F, Wind Speed in mph, Ozone in ppb (parts per billion)."
)
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Apply frame and hairlines, then finalize
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
