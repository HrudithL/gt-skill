import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns
# Island name is the row identifier (stub), size is the measure
gt = (
    GT(df, rowname_col="name")
    # Step 5(e): Format the size column as a number with thousands separators
    .fmt_number(columns=["size"], decimals=0, use_seps=True)
    # Step 5(a): Cell borders — hairline between rows + column-label bottom rule
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 3: Big Color — color the size column with Blues gradient
    .data_color(
        columns=["size"],
        palette="Blues",
        domain=[float(np.nanmin(df[["size"]].to_numpy())),
                float(np.nanmax(df[["size"]].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (Big Color present)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # washed-blue tint for Blues palette
        column_labels_font_weight="bold",
    )
    # Step 5(d): Stub tint — harmonized to washed-blue per grey-budget rule
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5(c): Row striping (≥10 rows and not fully covered by color)
    .opt_row_striping()
    # Step 6: Titles and annotations
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square kilometers",
    )
    .tab_source_note(source_note="Larger islands are shaded darker to show relative magnitude.")
    .tab_source_note(source_note="Source: islands.csv")
    # Frame: boxed light border on all sides
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

# Step 7: Render and verify
gt.gtsave("table.png", expand=15)
