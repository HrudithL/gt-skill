import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

# Read air quality data
df = pd.read_csv("airquality.csv")

# Compute monthly averages
monthly_summary = df.groupby("Month")[["Ozone", "Wind", "Temp"]].mean().round(2)
monthly_summary = monthly_summary.reset_index()

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
monthly_summary["Month"] = monthly_summary["Month"].map(month_names)

# Rename columns for display
monthly_summary = monthly_summary.rename(columns={
    "Month": "month",
    "Ozone": "ozone",
    "Wind": "wind",
    "Temp": "temp",
})

# Create the GT table
gt = GT(monthly_summary, rowname_col="month")
gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month"),
)
gt = gt.tab_stubhead(label="Month")

# Format the numeric columns
gt = gt.fmt_number(columns="temp", decimals=1)
gt = gt.fmt_number(columns="wind", decimals=2)
gt = gt.fmt_number(columns="ozone", decimals=2)

# Humanize column labels
gt = gt.cols_label(
    ozone="Ozone (ppb)",
    wind="Wind (mph)",
    temp="Temperature (°F)",
)

# Set column widths
gt = gt.cols_width(cases={
    "month": "120px",
    "temp": "130px",
    "wind": "130px",
    "ozone": "130px",
})

# Apply padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmaps: temperature and wind as sequential measures (neutral = Blues)
gt = heatmap(gt, ["temp", "wind"], kind="sequential", hue="neutral")

# Apply branding and styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = gt.tab_source_note(
    source_note="Temperature measured in degrees Fahrenheit, wind speed in miles per hour, and ozone in parts per billion."
)
gt = gt.tab_source_note(
    source_note="Source: provided air quality dataset."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
