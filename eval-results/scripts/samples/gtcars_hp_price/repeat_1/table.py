import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and rename for clarity
df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Ensure numeric types
df["Horsepower"] = pd.to_numeric(df["Horsepower"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

# Create stub: combine manufacturer and model for uniqueness
df["display_name"] = df["Manufacturer"] + " " + df["Model"]
df = df[["display_name", "Horsepower", "Price"]]
df.columns = ["Car", "Horsepower", "Price"]

# Step 2: Organize columns
# Stub is "Car", value columns are Horsepower and Price

# Step 3: Big Color - Price is the hero measure (neutral magnitude → Blues)
cols_price = ["Price"]
lo = float(np.nanmin(df[cols_price].to_numpy()))
hi = float(np.nanmax(df[cols_price].to_numpy()))

# Step 4: Create base table with stub
gt = GT(df, rowname_col="Car")

# Compact column sizing
gt = gt.cols_width(cases={"Car": "200px", "Horsepower": "120px", "Price": "140px"})

# Step 5: Small Color checklist
# (e) Formatting per column
gt = (gt
    .fmt_number(columns=["Horsepower"], decimals=0, use_seps=True)
    .fmt_currency(columns=["Price"], decimals=0, use_seps=True)
    .sub_missing(columns=["Horsepower", "Price"], missing_text="—")
)

# (a) Cell borders - hairlines
gt = (gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Padding for compact layout
        heading_padding="10px",
        column_labels_padding="10px",
        column_labels_padding_horizontal="10px",
        data_row_padding="6px",
        data_row_padding_horizontal="10px",
        source_notes_padding="10px",
    )
)

# Step 3 continued: Apply heatmap to Price column
gt = heatmap(gt, cols_price, kind="sequential", hue="neutral", domain=[lo, hi])

# (c) Row striping
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt)

# Step 4: Apply heading band
gt = band(gt)

# Step 6: Titles and annotations
gt = (gt
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="High-performance automobiles from premium manufacturers",
    )
    .tab_source_note("Source: gtcars.csv")
)

# Step 5: Frame and finalize
gt = frame(gt)
finalize(gt, "table.png")
