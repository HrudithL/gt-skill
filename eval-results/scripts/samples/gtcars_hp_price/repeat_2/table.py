import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select and organize columns
df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Ensure numeric columns are properly typed
df["Horsepower"] = pd.to_numeric(df["Horsepower"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

# Step 2: Organize columns with stub (rowname_col for Manufacturer)
gt = GT(df, rowname_col="Manufacturer")

# Step 3: Big Color - horsepower is the hero column (ordered magnitude ≥5 rows)
# Blues palette for neutral magnitude (no inherent good/bad direction)
gt = heatmap(gt, "Horsepower", kind="sequential", hue="positive")

# Step 4: Heading band - light band since we have Big Color
gt = band(gt, shade="light", hue="navy")

# Step 5: Small color polish
gt = (
    gt
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .fmt_number(columns="Horsepower", decimals=0)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A selection of high-performance vehicles"
    )
)

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Frame and finalize
gt = frame(gt)
finalize(gt, path="table.png")
