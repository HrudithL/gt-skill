import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Clean data
df = pd.read_csv("islands.csv")
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns (name is stub, size is measure)
gt = GT(df, rowname_col="name")

# Step 3: Big Color — size is ordered numeric magnitude (≥5 rows) → sequential Blues
gt = heatmap(gt, "size", kind="sequential", hue="positive")

# Step 4: Heading band — light band (Big Color present), washed-DA tint of Blues hue
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color checklist
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)

# Step 6: Titles & Annotations
gt = gt.tab_header(
    title="World's Largest Islands",
    subtitle="Island sizes in thousands of square kilometers"
)
gt = gt.tab_source_note("Source: provided dataset.")

# Step 7: Render
gt = frame(gt)
finalize(gt, "table.png")
