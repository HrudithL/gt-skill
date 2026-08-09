import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean the data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 2: Organize columns (name is stub, size is hero measure)
# Step 3: Compute domain for Big Color (Blues gradient for neutral magnitude)
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5: Build table with light band (Big Color present) and apply Small-Color checklist
gt = (
    GT(df, rowname_col="name")
    # Step 3: Big Color — Blues gradient for neutral magnitude (size)
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (pale blue, washed Navy tint)
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
    # Step 5d: Stub tint (harmonized to pale blue)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Global constant: Frame (boxed border on all sides)
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
    # Step 5c: Row striping (≥10 rows, body not fully filled)
    .opt_row_striping()
    # Titles
    .tab_header(
        title="Islands by Size",
        subtitle="Area in thousands of square miles",
    )
)

gt.gtsave("table.png", expand=15)
