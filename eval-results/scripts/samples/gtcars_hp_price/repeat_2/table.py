import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Keep only necessary columns
df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Sort by horsepower descending for better visual narrative
df = df.sort_values("Horsepower", ascending=False).reset_index(drop=True)

# Step 2: Organize columns with stub
# Use Manufacturer + Model as stub (row identifier)
df.insert(0, "Car", df["Manufacturer"] + " " + df["Model"])
df = df[["Car", "Horsepower", "Price"]].copy()

# Step 3 & 4: Build table with Big Color (two neutral magnitudes)
# Horsepower primary (mentioned first) → Blues
# Price secondary → Greens (fallback from Blues → Greens ladder)
gt = GT(df, rowname_col="Car")

# Format numbers
gt = (
    gt
    .fmt_number(columns="Horsepower", decimals=0)
    .fmt_currency(columns="Price", currency="USD", decimals=0)
)

# Apply Big Color — two gradient fills with heatmap helper
gt = heatmap(gt, "Horsepower", kind="sequential", hue="neutral")
gt = heatmap(gt, "Price", kind="sequential", hue="positive")

# Step 4: Apply heading band (light washed tint since Big Color present)
gt = band(gt, shade="light", hue="navy")

# Step 5: Apply Small Color polish
# Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Row striping (≥10 rows with Big Color)
if len(df) >= 10:
    gt = stripe(gt)

# Stub tint
gt = stub_tint(gt, hue="navy")

# Step 6: Add titles and annotations
gt = (
    gt
    .tab_header(
        title="GT Cars Database",
        subtitle="Horsepower and Price Comparison",
    )
    .tab_source_note(
        source_note="Data source: gtcars.csv",
    )
)

# Step 7: Apply frame and finalize
gt = frame(gt)
gt = finalize(gt)
