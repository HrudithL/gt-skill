import numpy as np
import pandas as pd
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.dropna()

# Step 2: Organize columns
gt = GT(df, rowname_col="name")

# Step 3: Big Color - size is an ordered numeric magnitude with ≥49 rows, qualifies for color
# Format the measure
gt = gt.fmt_number(columns=["size"], decimals=0, use_seps=True)

# Apply heatmap with sequential neutral palette (Blues for magnitude)
gt = heatmap(gt, columns="size", kind="sequential", hue="neutral")

# Step 4: Heading band (fixed navy branding)
gt = band(gt)

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Column widths and padding
gt = gt.cols_width(cases={"name": "140px", "size": "100px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
    .tab_source_note(source_note="Source: islands.csv")
)

# Step 7: Render
finalize(gt, path="table.png")
