import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and validate data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 2: Organize columns with stub
gt = GT(df, rowname_col="name")

# Step 3: Big Color - size qualifies (≥5 rows, numeric magnitude → Blues)
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)
gt = gt.data_color(
    columns="size",
    palette="Blues",
    domain=[lo, hi],
    truncate=False,
    na_color="#808080",
)

# Step 4: Heading band - fixed navy band
gt = gt.tab_options(
    heading_background_color="#08306B",
    heading_title_font_weight="bold",
    heading_align="center",
)
gt = gt.tab_style(
    style=style.text(color="white"),
    locations=loc.column_labels(),
)
gt = gt.tab_options(
    column_labels_background_color="#08306B",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small Color polish checklist
# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# (c) Row striping - apply by default
gt = gt.opt_row_striping()
gt = gt.tab_options(row_striping_background_color="#F6F6F6")

# (d) Stub tint
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# (f) Frame - boxed enclosing border
gt = gt.tab_options(
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

# Compact layout padding
gt = gt.cols_width(cases={"size": "100px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Island Sizes",
    subtitle="Size in thousands of square kilometers, sorted largest to smallest",
)

# Two separate source note calls for ≥5 rows
gt = gt.tab_source_note(
    source_note="Size measured in thousands of square kilometers.",
)
gt = gt.tab_source_note(
    source_note="Source: islands.csv",
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
