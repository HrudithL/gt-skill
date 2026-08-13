import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels
)

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Group by month and compute averages
monthly_avg = df.groupby("Month")[["Ozone", "Wind", "Temp"]].mean().reset_index()

# Round to one decimal place for readability
monthly_avg = monthly_avg.round(1)

# Map month numbers to names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly_avg["Month"] = monthly_avg["Month"].map(month_names)

# Create the GT table
gt = GT(monthly_avg, rowname_col="Month")
gt = gt.tab_header(
    title="Air Quality Metrics by Month",
    subtitle=md("Average temperature, wind speed, and ozone levels across each month"),
)

# Format the columns
gt = gt.fmt_number(columns=["Ozone", "Wind", "Temp"], decimals=1)

# Apply humanized labels with custom overrides
gt = humanize_labels(gt, monthly_avg)

# Set column widths and padding
gt = gt.cols_width(
    cases={
        "Month": "100px",
        "Ozone": "110px",
        "Wind": "110px",
        "Temp": "110px",
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

# Apply heatmaps for the three measures
# Ozone and Temperature are sequential (neutral Blue palette)
# Wind is sequential with a neutral/positive sense (Blue palette)
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")
gt = heatmap(gt, "Temp", kind="sequential", hue="neutral")
gt = heatmap(gt, "Wind", kind="sequential", hue="neutral")

# Apply house styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = gt.tab_source_note(
    source_note="All measurements are monthly averages; missing values in source data were excluded from calculations."
)
gt = gt.tab_source_note(
    source_note="Source: airquality.csv dataset."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
