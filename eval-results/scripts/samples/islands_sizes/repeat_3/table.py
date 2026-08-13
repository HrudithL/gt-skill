import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("islands.csv")

# Step 1: Data cleaning — verify the data
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns — name is the stub identifier
cols_measure = ["size"]

# Step 3: Big Color — ordered magnitude with >5 rows qualifies
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Build the table
gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Land area in thousands of km²"
    )
    .fmt_number(columns=cols_measure, decimals=0, use_seps=True)
    .sub_missing(columns=cols_measure, missing_text="—")
)

# Step 3: Apply heatmap — neutral magnitude uses sequential Blues
gt = heatmap(gt, cols_measure, kind="sequential", hue="neutral")

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = gt.cols_width(cases={"size": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Frame and render
gt = frame(gt)
finalize(gt, "table.png")
