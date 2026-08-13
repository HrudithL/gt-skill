import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Get top 10 by MSRP and sort by country then MSRP descending
top_10 = df.nlargest(10, "msrp").sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display name combining manufacturer and model
top_10["car_name"] = top_10["mfr"] + " " + top_10["model"]

# Select and rename columns for display
display_df = top_10[["ctry_origin", "car_name", "drivetrain", "trsmn", "msrp"]].copy()
display_df.columns = ["Country", "Car", "Drivetrain", "Transmission", "MSRP"]

# Step 2: Organize columns and construct GT with grouping
gt = GT(display_df, rowname_col="Car", groupname_col="Country")

# Rename columns for display
gt = gt.cols_label(
    Drivetrain="Drivetrain",
    Transmission="Transmission",
    MSRP="MSRP"
)

# Hide the Country column since it's now used as groupname_col
gt = gt.cols_hide(columns=["Country"])

# Move MSRP to the end (rightmost outer edge as the hero measure)
gt = gt.cols_move_to_end(columns=["MSRP"])

# Set column widths
gt = gt.cols_width(cases={
    "Drivetrain": "120px",
    "Transmission": "130px",
    "MSRP": "140px"
})

# Step 3: Big Color — MSRP gets the hero fill (neutral magnitude = Blues)
cols_to_color = ["MSRP"]
lo = float(np.nanmin(display_df[cols_to_color].to_numpy()))
hi = float(np.nanmax(display_df[cols_to_color].to_numpy()))

gt = gt.fmt_currency(columns=["MSRP"], currency="USD", decimals=0)

gt = gt.data_color(
    columns=cols_to_color,
    palette="Blues",
    domain=[lo, hi],
    truncate=False,
    na_color="#808080"
)

# Step 4: Heading band (fixed navy, already applied by tab_header)
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by Country of Origin with Drivetrain and Transmission Details"
)

# Step 5a: Cell borders — hairlines between all body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px"
)

# Step 5b: No column-group vertical dividers (no spanners in this table)

# Step 5c: Row striping (applied by default)
gt = gt.opt_row_striping()

# Step 5d: Stub tint (the Car column gets the fixed pale-blue tint)
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub()
)

# Step 5e: Row-group emphasis (bold + structural rule)
gt = gt.tab_options(
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px"
)

# Step 5f: Frame (boxed border on all sides)
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
    table_border_right_width="1px"
)

# Compact layout padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px"
)

# Step 6: Titles & annotations (two separate source note calls)
gt = gt.tab_source_note(
    source_note="MSRP represents the manufacturer's suggested retail price in U.S. dollars for the base model variant of each vehicle."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv"
)

# Step 7: Render and verify
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
