import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.dropna()  # Remove any trailing empty rows
df = df.astype({"name": "str", "size": "float"})

# Step 2: Organize columns
# Island name is the stub, size is the measure
# Sort by size descending for readability
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 3: Compute Big Color domain
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5: Build the table with heading band and Small-Color polish
gt = (
    GT(df, rowname_col="name")
    # Format the size column as a number
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color — column gradient fill for ordered magnitude
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — dark navy background with white text
    .tab_options(
        heading_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5a: Cell borders and hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
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
    # Step 5c: Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5d: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Compact layout — padding values
    .cols_width(cases={"size": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles and annotations
    .tab_header(
        title="Island Sizes Around the World",
        subtitle="Land area in thousands of square kilometers",
    )
    .tab_source_note(
        source_note="Sizes are ranked from largest to smallest.",
    )
    .tab_source_note(
        source_note="Source: Standard geographical reference data.",
    )
)

# Step 7: Render and verify
gt.gtsave("table.png", expand=15)
