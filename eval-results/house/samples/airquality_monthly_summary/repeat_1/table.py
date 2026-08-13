import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

# Read the data
df = pd.read_csv("airquality.csv")

# Group by month and calculate means
monthly = df.groupby("Month").agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean",
}).reset_index()

# Map month numbers to names for clarity
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly[["Month_Name", "Ozone", "Wind", "Temp"]]
monthly.rename(columns={"Month_Name": "Month"}, inplace=True)

# Round to 1 decimal
monthly = monthly.round(1)

# Create the GT table
gt = (
    GT(monthly, rowname_col="Month")
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average temperature, wind speed, and ozone levels"
    )
    .fmt_number(columns="Ozone", decimals=1)
    .fmt_number(columns="Wind", decimals=1)
    .fmt_number(columns="Temp", decimals=1)
    .cols_width(cases={
        "Month": "100px",
        "Ozone": "120px",
        "Wind": "120px",
        "Temp": "120px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Apply the sequential heatmap to Ozone (the primary measure of interest)
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")

# Wind and Temp stay plain text
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = (
    gt.tab_source_note(
        source_note="Ozone levels are shown in parts per billion (ppb); Wind speed in miles per hour; Temperature in Fahrenheit."
    )
    .tab_source_note(
        source_note="Source: airquality.csv dataset."
    )
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
