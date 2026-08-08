import pandas as pd
import numpy as np
from great_tables import GT

# Step 1: Read and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns — name is stub, size is the hero measure
gt = GT(df, rowname_col="name")

# Step 3: Big Color — size is a neutral magnitude, ≥5 rows
# Domain computed from data
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    gt
    .fmt_number(columns=cols, decimals=0)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band — light band with washed-blue tint
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small Color polish
gt = (
    gt
    .tab_options(
        table_border_left_color="#E8E8E8",
        table_border_left_width="1px",
        table_border_right_color="#E8E8E8",
        table_border_right_width="1px",
        table_border_top_color="#E8E8E8",
        table_border_top_width="1px",
        table_border_bottom_color="#E8E8E8",
        table_border_bottom_width="1px",
        row_striping_background_color="#F6F6F6",
    )
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
)

# Step 7: Render
gt.gtsave("table.png")
