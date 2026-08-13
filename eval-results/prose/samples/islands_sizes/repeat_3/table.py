import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Clean & understand data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 2: Organize columns (stub already correct — name is the identifier)
# Step 3: Big Color — size qualifies (≥5 rows, ordered magnitude)
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5: Build table with heading band, formatting, colors, and polish
gt = (
    GT(df, rowname_col="name")
    # Step 4: Heading band (fixed, every table)
    .tab_options(
        heading_background_color="#08306B",
        column_labels_background_color="#08306B",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5: Small Color polish — borders, striping, stub tint, formatting
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
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .opt_row_striping(row_striping=True)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Format numeric columns
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color — gradient fill for size
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
        subtitle="Area in thousands of square kilometers",
    )
    .cols_width(cases={"size": "120px"})
    .tab_source_note(
        source_note="Islands ordered by size, largest to smallest."
    )
    .tab_source_note(
        source_note="Source: World geographic data."
    )
)

gt.gtsave("table.png", expand=15)
