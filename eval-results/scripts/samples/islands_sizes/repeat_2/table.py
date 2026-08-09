import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Clean data
df = pd.read_csv("islands.csv")
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns — size is the hero measure
cols = ["size"]

# Step 3: Big Color — size qualifies (≥5 rows, ordered magnitude)
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5: Build the table with light band (Big Color present) and Small Color polish
gt = (
    GT(df, rowname_col="name")
    # Formatting
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .sub_missing(columns="size", missing_text="—")
    # Big Color: gradient fill on size
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Column labels — light band (washed Navy tint)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5(a): Cell borders — hairline between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5(c): Row striping (≥10 rows and not fully colored)
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5(d): Stub tint
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
    # Step 6: Titles and caption
    .tab_header(
        title="Island Sizes",
        subtitle="Geographic area in thousands of square kilometers",
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt.gtsave("table.png", expand=15)
