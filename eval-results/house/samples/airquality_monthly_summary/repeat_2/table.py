import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, heatmap, humanize_labels

# Read the air quality data
df = pd.read_csv("./airquality.csv")

# Create monthly summary: average Temp, Wind, and Ozone by Month
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).round(1).reset_index()

# Create month name labels
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]

# Build the table
gt = GT(monthly, rowname_col="Month_Name")
gt = gt.tab_header(
    title="Air Quality Summary by Month",
    subtitle=md("Average temperature, wind speed, and ozone levels")
)

# Format columns
gt = gt.fmt_number(columns="Temp", decimals=1)
gt = gt.fmt_number(columns="Wind", decimals=1)
gt = gt.fmt_number(columns="Ozone", decimals=1)

# Humanize labels
gt = humanize_labels(
    gt,
    monthly,
    overrides={"Month_Name": "Month"}
)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "Month_Name": "110px",
        "Temp": "110px",
        "Wind": "110px",
        "Ozone": "110px",
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

# Apply heatmap to Ozone (the main measure)
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")

# Small color polish
gt = stripe(gt)
gt = band(gt, hue="navy")

# Source notes
gt = gt.tab_source_note(
    source_note="Ozone levels reflect daily averages across all available measurements in the month."
)
gt = gt.tab_source_note(
    source_note="Source: R airquality dataset."
)

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
