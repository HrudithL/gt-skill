import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Load data
df = pd.read_csv("islands.csv")

# Sort by size descending for better readability
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Create GT table
gt = GT(df).tab_header(
    title="World Islands by Size",
    subtitle=md("Land area in thousands of square kilometers"),
).fmt_number(columns="size", decimals=1, use_seps=False)

# Apply humanize_labels
gt = humanize_labels(gt, df)

# Apply single heatmap for size (sequential, neutral = Blues)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply band and frame
gt = band(gt, hue="navy")
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Render
finalize(gt, path="table.png")
