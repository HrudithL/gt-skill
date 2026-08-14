import numpy as np
import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint, hairlines

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df["size"] = df["size"].astype(float)

# Step 2: Organize columns
# "name" is the row identifier (stub), "size" is the hero measure
# Already in correct order

# Step 3: Determine Big Color
# size is an ordered numeric magnitude over 48 rows → qualifies
# Neutral magnitude (size in thousands) → Blues palette
# Compute data-driven domain
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4: Build the table with heading band
gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns="size", decimals=0, use_seps=False)
)

# Apply heading band (Step 4)
gt = band(gt)

# Step 3: Apply heatmap (Big Color) with correct arguments
gt = heatmap(gt, columns="size", kind="sequential", hue="neutral", domain=[lo, hi])

# Step 5: Apply Small-Color polish
gt = stripe(gt)
gt = stub_tint(gt)

# Apply hairlines (cell borders)
gt = hairlines(gt)

# Column-label styling
gt = gt.tab_options(
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

gt = gt.tab_style(
    style=style.text(color="white"),
    locations=loc.column_labels()
)

# Apply compact layout with column widths and padding
gt = gt.cols_width(cases={"size": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Add titles and annotations
gt = (
    gt
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers"
    )
    .tab_source_note(
        "Displays the surface area of major islands worldwide."
    )
    .tab_source_note(
        "Source: Reference data"
    )
)

# Step 5: Apply frame and finalize layout
gt = frame(gt)

# Step 7: Render
finalize(gt)
