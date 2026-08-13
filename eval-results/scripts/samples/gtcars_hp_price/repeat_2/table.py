import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, stripe, stub_tint, frame, hairlines, finalize

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select relevant columns: model (stub), horsepower, and price
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create a display label combining manufacturer and model
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].copy()
df.columns = ["car", "hp", "msrp"]

# Step 2: Organize columns - car as stub, horsepower (plain), price (colored)
gt = GT(df, rowname_col="car")

# Step 3: Big Color - msrp is the hero (neutral magnitude → Blues)
# Domain computation
msrp_cols = ["msrp"]
lo = float(np.nanmin(df[msrp_cols].to_numpy()))
hi = float(np.nanmax(df[msrp_cols].to_numpy()))

gt = heatmap(gt, "msrp", kind="sequential", hue="neutral", domain=[lo, hi])

# Step 4: Heading band (fixed navy)
gt = band(gt)

# Step 5: Small Color polish
gt = frame(gt)
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Formatting per column type
gt = gt.fmt_number(columns="hp", decimals=0, use_seps=True)
gt = gt.fmt_currency(columns="msrp", decimals=0, use_seps=True)

# Column widths
gt = gt.cols_width(cases={"hp": "100px", "msrp": "120px"})

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Performance and Pricing",
    subtitle="GT Cars Horsepower and MSRP"
)

gt = gt.tab_source_note(
    source_note="Price reflects base model MSRP. Horsepower is at rated RPM."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv"
)

# Step 7: Render
finalize(gt, "table.png")
