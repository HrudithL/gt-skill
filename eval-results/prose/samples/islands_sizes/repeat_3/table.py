import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Understand and clean the data
df = pd.read_csv("islands.csv")
# Data is clean: name (string) and size (int, in thousands of km²)
# 49 rows, one numeric magnitude measure, island names as identifiers

# Step 2: Organize columns
# name → stub (row identifier), size → measure column (outer edge/right)
# The size column will be our colored measure (≥5 rows, ordered magnitude)

# Step 3: Big Color — size is an ordered magnitude over 49 rows
# From REFERENCE.md & column_gradient_fill.md: neutral magnitude → Blues palette
lo = float(np.nanmin(df[["size"]].to_numpy()))
hi = float(np.nanmax(df[["size"]].to_numpy()))

# Step 4 & 5: Build the table with heading band, padding, and small-color checklist
gt = (
    GT(df, rowname_col="name")
    # Step 2: Column organization & labeling
    .cols_label(size="Size (1000s km²)")
    # Step 5(a): Cell borders (hairlines between rows)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Frame — boxed border on all four sides (from small_color.md)
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
    )
    # Step 5(c): Row striping (applied by default, body is not 100% colored at measure level)
    .opt_row_striping()
    # Step 5(d): Stub tint (fixed branding pale-blue)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5(e): Format the size column as a number
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color — data_color for the size measure
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 6: Titles & annotations
    .tab_header(
        title="Islands by Size",
        subtitle="Area measurements in thousands of square kilometers",
    )
    # Footer: two calls — analytical caption + source note (≥5 rows)
    .tab_source_note(
        "The largest islands shown are continental-scale landmasses (Africa, Asia, North America), "
        "followed by major islands (Greenland, New Guinea, Borneo, Madagascar)."
    )
    .tab_source_note("Data source: Island size reference dataset")
)

# Step 7: Render and verify
# Frame outer margin expand=15 from small_color.md, zoom=2.0 default
gt.gtsave("table.png", expand=15, zoom=2.0)
print("Table rendered successfully: table.png")
