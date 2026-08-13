import pandas as pd
import numpy as np
from great_tables import GT
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Create monthly summary: average temperature, wind speed, and ozone
monthly = df.groupby("Month").agg(
    Temperature=("Temp", "mean"),
    Wind=("Wind", "mean"),
    Ozone=("Ozone", "mean"),
).reset_index()

# Map month numbers to names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

# Round to 1 decimal place
monthly["Temperature"] = monthly["Temperature"].round(1)
monthly["Wind"] = monthly["Wind"].round(1)
monthly["Ozone"] = monthly["Ozone"].round(1)

# Create the GT table
gt = (
    GT(monthly, rowname_col="Month")
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average temperature, wind speed, and ozone levels by month",
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns=["Temperature", "Wind", "Ozone"], decimals=1)
    .sub_missing(columns=["Temperature", "Wind", "Ozone"], missing_text="—")
)

# Humanize column labels
gt = humanize_labels(gt, monthly)

# Set column widths
gt = gt.cols_width(
    cases={
        "Month": "100px",
        "Temperature": "120px",
        "Wind": "120px",
        "Ozone": "120px",
    }
)

# Set padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmaps for the three measures (all are magnitudes, sequential/neutral)
gt = heatmap(gt, "Temperature", kind="sequential", hue="neutral")
gt = heatmap(gt, "Wind", kind="sequential", hue="neutral")
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")

# Apply styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = (
    gt.tab_source_note(
        source_note="Values are monthly averages across all days in the dataset."
    )
    .tab_source_note(
        source_note="Source: New York air quality data (May-September)."
    )
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
