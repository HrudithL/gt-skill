import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Read the islands data
df = pd.read_csv("islands.csv")

# Create the GT table
gt = GT(df, rowname_col="name")

# Add title and subtitle
gt = gt.tab_header(
    title="Island Sizes",
    subtitle=md("Surface area of the world's largest islands in thousands of square kilometers"),
)

# Format the size column with thousands separator
gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)

# Humanize labels
gt = humanize_labels(gt, df)

# Apply the sequential heatmap to size column (Blues for neutral magnitude)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply heading band
gt = band(gt, hue="navy")

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Apply the frame
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
