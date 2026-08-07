import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("islands.csv")
# Data is already clean: name column (object), size column (int64)

# Step 2: Organize columns
# "name" is the stub (row identifier), "size" is the measure
# No grouping, no spanners

# Step 3: Big Color
# Size is an ordered numeric magnitude with 48 rows (≥5) → qualifies for gradient fill
# Palette: "size" is a neutral magnitude (quantity/count) → Blues (palettes.md §3)
cols_to_color = ["size"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    # Step 5a: Cell borders — always
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5c: Row striping (≥10 body rows and not fully filled by Big Color)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5d: Stub tint (stub exists; grey default, will harmonize later if needed)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Step 5e: Formatting per column
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .sub_missing(columns="size", missing_text="—")
    # Step 3: Big Color — gradient fill
    .data_color(
        columns=cols_to_color,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (has Big Color → LIGHT band with washed Navy tint)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
    )
    # Step 6: Titles & Annotations
    .tab_header(
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers",
    )
    # Step 5: Frame — boxed enclosing border
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

# Step 7: Render & Verify
gt.gtsave("table.png", expand=15)
