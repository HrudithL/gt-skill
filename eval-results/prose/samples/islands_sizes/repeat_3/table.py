import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns
# name is the stub, size is the measure
# Ensure size is numeric
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 3: Big Color — compute domain for size gradient
cols_measure = ["size"]
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Step 4 & 5 & 6: Build the table
gt = (
    GT(df, rowname_col="name")
    # Column label
    .cols_label(size="Size (1000 km²)")
    # Format the size column
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color — gradient fill for size (neutral magnitude → Blues)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed navy, white text)
    .tab_header(
        title="World's Largest Islands",
        subtitle="Island sizes in thousands of square kilometers",
    )
    # Step 5: Small Color polish
    # (a) Cell borders — hairlines and column-label bottom rule
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
    # Compact layout padding
    .cols_width(cases={"name": "200px", "size": "140px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & annotations — two footer calls
    .tab_source_note(source_note="Data represents island land area in thousands of square kilometers.")
    .tab_source_note(source_note="Source: islands.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
