import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df[df["name"].notna()]  # Remove any empty rows
df = df.reset_index(drop=True)

# Step 2: Organize columns
# name is the stub, size is the measure
# size qualifies for gradient fill (ordered numeric, ≥5 rows)

# Step 3: Determine which measure(s) earn the fill
# size is the only measure and qualifies (ordered magnitude, ≥5 rows)
cols_to_color = ["size"]

# Build the table
gt = (
    GT(df, rowname_col="name")
    .fmt_integer(columns="size", use_seps=True)
    .cols_width(cases={"name": "200px", "size": "120px"})
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square kilometers"
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 3: Apply heatmap color to the size column
gt = heatmap(gt, columns="size", kind="sequential", hue="neutral")

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Apply stub tint and striping
gt = stub_tint(gt)
gt = stripe(gt)
gt = frame(gt)

# Step 6: Add titles and annotations
gt = gt.tab_source_note(
    source_note="Island sizes measured in thousands of square kilometers."
)

# Render
finalize(gt)
