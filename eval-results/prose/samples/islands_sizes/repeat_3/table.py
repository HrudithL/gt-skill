import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns — name is stub, size is measure
# 49 islands (rows ≥ 10) → proceed with striping and color

# Step 3: Big Color — size is ordered magnitude (≥5 rows)
# Palette: Blues (neutral magnitude per palettes.md §3)
cols_measure = ["size"]
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Step 4 & 5: Build the table
gt = (
    GT(df, rowname_col="name")
    # Column labels
    .cols_label(size="Size")
    # Format
    .fmt_number(columns=cols_measure, decimals=0, use_seps=True)
    .sub_missing(columns=cols_measure, missing_text="—")
    # Step 3: Big Color gradient
    .data_color(
        columns=cols_measure,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light band (Big Color present)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (≥10 rows, not fully filled by Big Color)
    .opt_row_striping()
    # (d) Stub tint (washed-DA tint for Big Color)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame border (all four sides)
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
    # Step 6: Titles + caption
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers",
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

# Render
gt.gtsave("table.png", expand=15)
