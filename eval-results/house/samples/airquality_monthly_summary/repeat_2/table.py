import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

df = pd.read_csv("airquality.csv")

# Group by month and compute monthly averages
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Create month name mapping
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["month_name"] = monthly["Month"].map(month_names)

# Reorder columns and select for display
monthly = monthly[["month_name", "Temp", "Wind", "Ozone"]].copy()
monthly.columns = ["month", "temp", "wind", "ozone"]

# Round to 1 decimal place for display
monthly["temp"] = monthly["temp"].round(1)
monthly["wind"] = monthly["wind"].round(1)
monthly["ozone"] = monthly["ozone"].round(1)

# Create the GT table
gt = (
    GT(monthly, rowname_col="month")
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle=md("Average temperature, wind speed, and ozone levels by month")
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns=["temp", "wind", "ozone"], decimals=1)
)

# Apply humanize labels
gt = humanize_labels(
    gt,
    monthly,
    overrides={"month": "Month", "temp": "Avg Temp (°F)", "wind": "Avg Wind (mph)", "ozone": "Avg Ozone (ppb)"}
)

# Column widths
gt = gt.cols_width(
    cases={
        "month": "120px",
        "temp": "120px",
        "wind": "120px",
        "ozone": "120px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmaps to the three measures
gt = heatmap(gt, "temp", kind="sequential", hue="neutral")
gt = heatmap(gt, "wind", kind="sequential", hue="neutral")
gt = heatmap(gt, "ozone", kind="sequential", hue="warning")

# Apply formatting
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = (
    gt.tab_source_note(
        source_note="Data represents monthly averages across all observed days in each month."
    )
    .tab_source_note(
        source_note="Source: R's airquality dataset."
    )
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
