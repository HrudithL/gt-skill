import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Read and clean data
df = pd.read_csv("islands.csv")
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns
cols_measure = ["size"]

# Step 3: Big Color — column gradient fill
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Step 4: Build the table with header band + Step 5 polish
gt = (
    GT(df, rowname_col="name")
    # Titles (Step 6)
    .tab_header(
        title="Islands by Size",
        subtitle="Comparing the areas of major world islands"
    )
    # Formatting (Step 5e)
    .fmt_integer(columns="size", use_seps=True)
    # Big Color (Step 3)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080"
    )
    # Heading band (Step 4)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px"
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels()
    )
    # Small Color (Step 5)
    # (a) Cell hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px"
    )
    # (c) Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6"
    )
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
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
        table_border_right_width="1px"
    )
    # Compact layout
    .cols_width(cases={"size": "100px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px"
    )
    # Footer notes (Step 6f) — two separate calls
    .tab_source_note(source_note="Size measured in thousands of square kilometers.")
    .tab_source_note(source_note="Source: islands.csv")
)

gt.gtsave("table.png", expand=15)
