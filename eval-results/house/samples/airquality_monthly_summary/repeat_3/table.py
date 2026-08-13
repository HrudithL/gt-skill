import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
df["Month"] = df["Month"].map(month_names)

# Group by month and calculate averages
monthly_data = df.groupby("Month", as_index=False)[["Ozone", "Wind", "Temp"]].mean()

# Round to 1 decimal place for display
monthly_data = monthly_data.round(1)

# Create GT table with Month as stub
gt = GT(monthly_data, rowname_col="Month")

# Add header and subtitle
gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month")
)

# Add stub header label
gt = gt.tab_stubhead(label="Month")

# Format columns
gt = gt.fmt_number(columns="Temp", decimals=1)
gt = gt.fmt_number(columns="Wind", decimals=1)
gt = gt.fmt_number(columns="Ozone", decimals=1)

# Humanize labels and add custom overrides
gt = humanize_labels(
    gt,
    monthly_data,
    overrides={
        "Ozone": "Ozone (ppb)",
        "Wind": "Wind Speed (mph)",
        "Temp": "Temperature (°F)"
    }
)

# Set column widths
gt = gt.cols_width(
    cases={
        "Month": "100px",
        "Ozone": "120px",
        "Wind": "130px",
        "Temp": "120px",
    }
)

# Apply padding and spacing
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply Big Color: heatmap all three measures (all are hero measures)
# Temperature: sequential (magnitude)
gt = heatmap(gt, "Temp", kind="sequential", hue="positive")
# Wind: sequential (magnitude)
gt = heatmap(gt, "Wind", kind="sequential", hue="positive")
# Ozone: sequential (magnitude)
gt = heatmap(gt, "Ozone", kind="sequential", hue="warning")

# Apply styling helpers
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = gt.tab_source_note(
    source_note="All values represent monthly averages from the air quality dataset."
)
gt = gt.tab_source_note(
    source_note="Source: provided air quality dataset."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
