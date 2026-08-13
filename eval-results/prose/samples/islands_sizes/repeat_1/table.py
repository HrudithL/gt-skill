import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 2: Organize columns (name is the stub, size is the measure)
cols_measure = ["size"]

# Step 3: Compute domain for color fill
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Step 4: Build the table
gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square miles"
    )
    .fmt_number(columns=cols_measure, decimals=1, use_seps=True)
    .data_color(
        columns=cols_measure,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 5: Small Color Polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (c) Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 4: Heading band
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Frame border
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
    # Compact layout
    .cols_width(cases={"name": "150px", "size": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & annotations
    .tab_source_note(source_note="Source: World island size data")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
