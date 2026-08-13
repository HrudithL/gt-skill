import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import band, stripe, stub_tint, finalize, heatmap, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 2: Organize columns
# Stub is "name" (island identifiers), measure is "size"
# Step 3: Compute domain for Big Color
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Build table
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
)

# Step 4: Heading band
gt = gt.tab_options(
    column_labels_background_color="#08306B",
    column_labels_font_weight="bold",
)
band(gt)

# Step 5: Small-Color polish
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .cols_width(cases={"size": "100px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
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

# Step 6: Titles & annotations
gt = (
    gt
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square kilometers",
    )
    .tab_source_note(source_note="Islands ranked by size, largest to smallest.")
    .tab_source_note(source_note="Source: islands.csv")
)

# Step 7: Render
finalize(gt)
gt.gtsave("table.png", expand=15)
