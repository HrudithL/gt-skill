import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, finalize, band, heatmap, humanize_labels
)

# Read the islands data
islands = pd.read_csv("islands.csv")

# Create the GT table
gt = GT(islands).tab_header(
    title="Islands by Size",
    subtitle="Geographic area in thousands of square kilometers",
).tab_source_note(
    source_note="Source: provided dataset."
)

# Format columns
gt = (
    gt.fmt_number(columns="size", decimals=1, use_seps=True)
    .cols_label(name="Island", size="Size (1000 km²)")
)

# Apply the sequential heatmap to the size column
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply the band styling
gt = band(gt, hue="navy")

# Apply the frame
gt = frame(gt)

# Finalize and save
finalize(gt)
