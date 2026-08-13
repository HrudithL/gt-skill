import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize

# Step 1: Load and clean the data
df = pd.read_csv("gtcars.csv")

# Select relevant columns: manufacturer, model, hp, msrp
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create a combined identifier for uniqueness (mfr + model)
df["car_name"] = df["mfr"] + " " + df["model"]
df = df.drop(columns=["mfr", "model"])

# Reorder columns: car_name (stub), hp, msrp
df = df[["car_name", "hp", "msrp"]]

# Ensure numeric columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Remove rows with missing critical values
df = df.dropna(subset=["hp", "msrp"])

# Step 2: Create the GT table with car_name as stub
gt = (
    GT(df, rowname_col="car_name")
    .cols_label(hp="Horsepower", msrp="Price (MSRP)")
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", currency="USD")
)

# Step 3: Apply Big Color - only price is colored (hero measure)
# Horsepower stays plain per the redundancy rule in small_color.md
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Apply small color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Step 6: Add titles and annotations
gt = (
    gt
    .tab_header(
        title="GT Cars: Horsepower vs Price",
        subtitle="2014-2017 performance vehicles"
    )
    .tab_source_note(
        md("Data represents MSRP pricing and horsepower ratings for performance vehicles from 2014-2017.")
    )
    .tab_source_note(
        md("Price encoded by magnitude; horsepower shown for reference.")
    )
)

# Step 7: Render
finalize(gt, "table.png")
