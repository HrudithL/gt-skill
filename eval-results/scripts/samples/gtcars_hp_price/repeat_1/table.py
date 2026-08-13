import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Read and clean the data
df = pd.read_csv("gtcars.csv")

# Create a composite stub: mfr + model for readability and uniqueness
df["car"] = df["mfr"] + " " + df["model"]

# Select only the columns we need: stub, hp, msrp
df_display = df[["car", "hp", "msrp"]].copy()

# Step 2: Organize columns
gt = GT(df_display, rowname_col="car")

# Step 3: Color the primary measure (msrp) using the heatmap helper
# Price is a neutral magnitude, so hue="neutral" → Blues palette
gt = heatmap(
    gt,
    columns="msrp",
    kind="sequential",
    hue="neutral",
)

# Step 4: Heading band
gt = band(gt)

# Step 5a: Cell borders and column-label styling
gt = hairlines(gt)

# Step 5d: Stub tint
gt = stub_tint(gt)

# Step 5c: Row striping
gt = stripe(gt)

# Step 5e: Formatting
gt = (
    gt.fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0, use_seps=True)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Step 5g: Compact layout
gt = gt.cols_width(cases={"car": "180px", "hp": "90px", "msrp": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="High-performance sports and luxury vehicles",
    )
    .tab_source_note(source_note="Price (MSRP) represents the manufacturer's suggested retail price and is the primary measure of value.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Frame (Step 5/render parameters) and finalize
gt = frame(gt)
finalize(gt, "table.png")
