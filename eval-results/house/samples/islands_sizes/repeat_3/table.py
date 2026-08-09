import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

# Read the data
df = pd.read_csv("islands.csv")

# Create the GT table
gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Land area by island",
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

# Color the size column with a sequential heatmap
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply heading band with navy accent
gt = band(gt, hue="navy")

# Apply striping (>= 10 rows and not fully colored)
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue="navy")

# Apply structural elements
gt = hairlines(gt)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Finalize and render
finalize(gt, path="table.png")
