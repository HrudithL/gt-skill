import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")

# Step 2: Organize columns
# 'name' is the identifier (stub), 'size' is the measure
gt = (
    GT(df, rowname_col="name")
    # Step 3: Big Color — size is an ordered magnitude measure (≥5 rows)
    # Compute the domain from the data
    .data_color(
        columns="size",
        palette="Blues",
        domain=[float(np.nanmin(df["size"].to_numpy())), float(np.nanmax(df["size"].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed navy, white text)
    .tab_header(
        title="Islands of the World",
        subtitle="Land area in thousands of square miles",
    )
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # Step 5: Small Color polish
    # (a) Cell borders — hairline between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Format the size column as a number
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .sub_missing(columns="size", missing_text="—")
    # Step 6: Titles & annotations
    .tab_source_note(source_note="Islands are ordered by size; the measure includes only the named island or island group.")
    .tab_source_note(source_note="Source: R datasets package.")
    # Frame — boxed enclosing border on all four sides
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Compact layout: set column widths
    .cols_width(cases={"size": "120px"})
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
