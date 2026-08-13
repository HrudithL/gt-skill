import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

# STEP 1: Read and clean data
df = pd.read_csv("gtcars.csv")

# Convert msrp to numeric (already numeric in this file)
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()

# Create a display name combining manufacturer and model
top10["car"] = top10["mfr"] + " " + top10["model"]

# Create a clean drivetrain/transmission label
top10["drivetrain_transmission"] = top10["drivetrain"].str.upper() + " / " + top10["trsmn"].str.upper()

# Keep year as numeric
top10["year"] = top10["year"].astype(int)

# Sort by country then by price descending for good grouping
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select final columns for display
# Order: Country (groupname_col), Car (rowname_col), Year, Drivetrain/Transmission, Price
final_df = top10[["ctry_origin", "car", "year", "drivetrain_transmission", "msrp"]].copy()
final_df.columns = ["Country", "Car", "Year", "Drivetrain / Transmission", "Price"]
final_df = final_df.reset_index(drop=True)

# STEP 2: Organize columns with grouping by country
# Country will be the groupname_col for row groups
# Car will be the rowname_col (stub) for row identifiers
gt = GT(final_df, rowname_col="Car", groupname_col="Country")

# STEP 5(e): Formatting
gt = (
    gt
    .fmt_number(columns=["Year"], decimals=0)
    .fmt_currency(columns=["Price"], currency="USD", decimals=0)
)

# STEP 3: Big Color - Price as the hero measure (ordered magnitude, ≥5 rows)
gt = heatmap(gt, "Price", kind="sequential", hue="neutral")

# STEP 4: Apply heading band (fixed branding)
gt = band(gt)

# STEP 5(c): Row striping
gt = stripe(gt)

# STEP 5(d): Stub tint
gt = stub_tint(gt)

# STEP 5(a): Cell borders (hairline already set by frame/finalize helpers)
gt = (
    gt
    .cols_width(cases={"Car": "200px", "Year": "60px", "Drivetrain / Transmission": "140px", "Price": "110px"})
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Add frame (enclosing border)
gt = frame(gt)

# STEP 6: Add titles and annotations
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="By country of origin with drivetrain and transmission details"
    )
    .tab_source_note(
        "Data includes the ten highest-priced sports cars from the gtcars dataset, grouped by their country of manufacture."
    )
    .tab_source_note(
        "Source: gtcars.csv"
    )
)

# STEP 7: Render
finalize(gt, "table.png")
