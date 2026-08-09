import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.dropna()  # remove empty rows
df = df.reset_index(drop=True)

# Step 2: Organize columns (name as stub, size as hero measure)
cols_measure = ["size"]

# Step 3: Big Color — compute domain for Blues gradient
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Build the table
gt = (
    GT(df, rowname_col="name")
    # Step 3: Big Color — gradient fill for size column
    .fmt_number(columns=cols_measure, decimals=1, use_seps=True)
    .data_color(
        columns=cols_measure,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — light washed-blue tint (Big Color present)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders — hairlines between body rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (≥10 rows and body not fully filled)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Frame — boxed border on all four sides
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
    # Step 6: Titles & Annotations
    .tab_header(
        title="Island Sizes",
        subtitle="Land area of major islands worldwide (thousands of km²)",
    )
    .tab_source_note(source_note="Size measured in thousands of square kilometers; gradient indicates relative magnitude.")
    .tab_source_note(source_note="Source: islands.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15, zoom=2.0)
