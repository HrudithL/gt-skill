import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
# Data is already clean: name (string) and size (numeric)

# Step 2: Organize columns
# "name" is the stub (row identifier), "size" is the measure
# No grouping, no additional organization needed

# Step 3: Big Color
# size is an ordered numeric magnitude over 49 rows → qualifies for column gradient
# Semantic: neutral magnitude (population/size) → Blues palette
cols_to_color = ["size"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))

# Step 4 & 5: Build the table with heading band, formatting, and polish
gt = (
    GT(df, rowname_col="name")
    # Step 3: Big Color - column gradient for size
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - LIGHT band (washed-blue for Blues table)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5c: Row striping (≥10 rows and not fully filled by Big Color)
    .opt_row_striping()
    # Step 5d: Stub tint (harmonized to washed-blue for Blues table)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Titles and annotations
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Land area in thousands of square kilometers",
    )
    # Frame border (global constant)
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

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("✓ table.png created successfully")
