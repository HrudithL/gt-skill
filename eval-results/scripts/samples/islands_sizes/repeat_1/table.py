import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns
# 'name' is the row identifier (stub), 'size' is the measure to color
df = df[df["size"].notna()].reset_index(drop=True)

# Step 3 & 4: Compute domain for Big Color (gradient fill on 'size')
cols_to_color = ["size"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))

# Step 5: Build the table with all formatting
gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (Big Color present) + washed-DA tint
    .tab_options(
        column_labels_background_color="#EAF0F6",  # washed Navy for Blues palette
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish checklist
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (>10 rows, not fully filled)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint (washed-DA to harmonize with Big Color)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame border (all four sides)
    .tab_options(
        table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
        table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
    )
    # Titles
    .tab_header(
        title="Island Sizes Around the World",
        subtitle="Area in thousands of square kilometers",
    )
    # Caption for >5 rows
    .tab_source_note(
        source_note="Data represents the areas of major islands worldwide, with larger islands shown in darker blue."
    )
)

gt.gtsave("table.png", expand=15)
