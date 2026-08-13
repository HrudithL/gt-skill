import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and understand data
df = pd.read_csv("gtcars.csv")

# Step 1: Data cleaning
# Columns are already properly typed; msrp is numeric
# No currency symbols, no object dtype issues to fix

# Get the top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Build a composite stub: mfr + model
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Select and organize columns
# Group by country, so we'll use groupname_col
# Stub: car name
# Measures: msrp (hero), drivetrain, trsmn (transmission)
display_cols = ["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]
top_10 = top_10[display_cols].copy()

# Sort by country then by msrp descending within country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Step 2: Organize columns
# Stub: car (the composite identifier)
# Group: ctry_origin (country)
# Display columns order: drivetrain, trsmn, msrp (hero measure at right edge)
gt = GT(
    top_10,
    rowname_col="car",
    groupname_col="ctry_origin"
)

# Step 3: Big Color - msrp is ordered magnitude, ≥5 rows qualifies
# Compute domain for msrp
cols_measure = ["msrp"]
lo = float(np.nanmin(top_10[cols_measure].to_numpy()))
hi = float(np.nanmax(top_10[cols_measure].to_numpy()))

gt = (
    gt
    .fmt_currency(columns="msrp", currency="USD")
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Hide the helper columns from display - the group column appears as a row group label
gt = gt.cols_hide(columns=["ctry_origin"])

# Step 4: Heading band - fixed navy band, bold labels, white text
gt = (
    gt
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
)

# Step 5: Small Color - polish checklist
# (a) Cell borders - hairline between all body rows
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# (b) Row striping - apply by default
gt = gt.opt_row_striping()

# (d) Stub tint - pale blue for the stub column
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# (c) Row group tint - group rows emphasis (bold + border)
gt = gt.tab_style(
    style=style.fill(color="#F0F0F0"),
    locations=loc.summary(rows=True),
)

# Frame - boxed border on all four sides
gt = gt.tab_options(
    table_border_top_style="solid",
    table_border_top_color="#E8E8E8",
    table_border_top_width="1px",
    table_border_bottom_style="solid",
    table_border_bottom_color="#E8E8E8",
    table_border_bottom_width="1px",
    table_border_left_style="solid",
    table_border_left_color="#E8E8E8",
    table_border_left_width="1px",
    table_border_right_style="solid",
    table_border_right_color="#E8E8E8",
    table_border_right_width="1px",
)

# Compact layout padding
gt = gt.opt_horizontal_padding(scale=1.2).opt_vertical_padding(scale=1.2)

# Step 6: Titles & annotations
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .tab_source_note(
        source_note="MSRP values shown in USD; cars ranked by price within each country"
    )
    .tab_source_note(
        source_note="Source: gtcars dataset"
    )
)

# Step 7: Render & verify
gt.gtsave("table.png")
print("Table saved to table.png")
