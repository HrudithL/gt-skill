import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# STEP 1: Understand & clean the data
df = pd.read_csv("islands.csv")
# Data is clean: island names (string) and sizes (numeric)

# STEP 2: Organize columns — island name is the stub
# No grouping needed; no column hiding
gt = GT(df, rowname_col="name")

# STEP 3: Big Color — size is an ordered magnitude (≥5 rows)
# Palette: Blues (neutral magnitude)
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    gt
    .fmt_number(columns=cols, decimals=0, use_seps=True)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# STEP 4: Heading band — light band (Blues Big Color present)
# Band color: washed-DA tint pale-blue #EAF0F6
gt = (
    gt
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# STEP 5: Small Color polish
# (a) Cell borders — hairlines between all body rows
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# (c) Row striping — 48 rows, not fully filled by Big Color
# NOTE: Stub tint and striping are mutually exclusive; striping is ON so stub tint is OFF
gt = gt.opt_row_striping()

# (e) Formatting — size already formatted as number with separators above

# Frame — boxed border on all four sides + margin
gt = (
    gt
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
)

# STEP 6: Titles & annotations
gt = (
    gt
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers"
    )
    .tab_source_note(source_note="Size ranges from 12,000 km² (Axel Heiberg) to 11,506,000 km² (Africa).")
    .tab_source_note(source_note="Source: islands.csv")
)

# STEP 7: Render & verify
gt.gtsave("table.png", expand=15)
