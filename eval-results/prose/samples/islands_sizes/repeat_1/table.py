import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.dropna(subset=["size"])  # remove any rows with missing size
df["size"] = pd.to_numeric(df["size"], errors="coerce")
df = df.dropna(subset=["size"])  # remove rows where size didn't convert

# Step 2: Organize columns (name as stub, size as measure)
# Size is an ordered numeric magnitude over 49 rows (≥5), so it qualifies for gradient fill

# Step 3: Compute domain for size
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Build the table
gt = (
    GT(df, rowname_col="name")
    # Step 6: Titles
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Area measurements in thousands of square kilometers",
    )
    # Step 5: Small Color - body hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 4: Heading band (unconditional) — dark navy band with white text
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.header(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.header(),
    )
    # Step 5: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Row striping
    .opt_row_striping()
    # Step 5: Format size as integer with thousands separator
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color - gradient fill for size (ordered magnitude)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Column labels
    .cols_label(size="Size (thousands km²)")
    .cols_width(cases={"name": "200px", "size": "150px"})
    # Step 5: Frame with border and compact layout padding
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
)

# Step 6: Footer - two separate notes (analytical caption + source)
gt = gt.tab_source_note("Islands ranked by area in thousands of square kilometers.")
gt = gt.tab_source_note("Data source: islands.csv")

# Step 7: Render with outer margin
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
