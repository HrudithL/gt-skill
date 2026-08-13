import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.copy()

# Ensure size is numeric (already should be)
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns - Island name is the stub, size is the measure
# Step 3: Big Color - size is an ordered magnitude over ≥5 rows, qualifies for column gradient
# Compute domain from data
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4: Build table with heading band
gt = (
    GT(df, rowname_col="name")
    # Step 3: Data color for the size measure (Blues palette for neutral magnitude)
    .data_color(
        columns=["size"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - dark navy, white text
    .tab_header(
        title="World's Largest Islands",
        subtitle="Island sizes in thousands of square kilometers",
    )
    .tab_options(
        heading_background_color="#08306B",
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # Step 5a: Cell borders - hairline between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5c: Row striping (not skipped - body has measure column plus stub)
    .opt_row_striping()
    # Step 5d: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5e: Formatting - number with 0 decimals and thousands separator
    .fmt_number(columns=["size"], decimals=0, use_seps=True)
    # Step 5: Frame - boxed border on all sides
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
    # Padding for compact layout and striping color
    .cols_width(cases={"size": "120px"})
    .tab_options(
        row_striping_background_color="#F6F6F6",
    )
    # Step 6: Titles & annotations - two footer calls
    .tab_source_note(source_note="Island sizes in thousands of square kilometers; includes continents for reference.")
    .tab_source_note(source_note="Source: Reference geographic data.")
)

# Step 7: Render and save
gt.gtsave("table.png", expand=15)
