import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns
# 'name' is the island identifier (stub), 'size' is the measure
gt = GT(df, rowname_col="name")

# Step 3: Big Color — size is ordered magnitude over ≥5 rows, qualifies for gradient fill
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    gt
    .fmt_number(columns=cols, decimals=1, use_seps=True)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band — light washed-DA tint (pale blue for Blues table)
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small Color polish
gt = (
    gt
    # (a) Cell borders — light hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping — ≥10 rows and body not fully filled by Big Color
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint — harmonize to washed-DA tint (pale blue for Blues table)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame — boxed border on all sides
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

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="Island Sizes",
        subtitle="Land area by island",
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
