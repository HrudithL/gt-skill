import pandas as pd
from great_tables import GT, loc
from house_table import PALETTE, frame, hairlines, finalize, stripe, stub_tint, heatmap

# Read and prepare data
df = pd.read_csv("gtcars.csv")

# Create composite row identifier and select relevant columns
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].copy()
df.columns = ["Car", "Horsepower", "Price"]

# Format price as currency (divide by 1 to keep as float, finalize will format)
df["Price"] = df["Price"].astype(float)

# Create GT table
gt = (
    GT(df, rowname_col="Car")
    .tab_header(
        title="GT Cars Performance",
        subtitle="Horsepower and pricing for high-performance vehicles"
    )
    .fmt_number(columns="Horsepower", decimals=0)
    .fmt_currency(columns="Price", currency="USD")
    .tab_source_note(
        source_note="Horsepower is the primary performance measure; price shown for reference."
    )
    .tab_source_note(
        source_note="Source: provided dataset."
    )
)

# Apply styling
gt = frame(gt)
gt = hairlines(gt)
gt = heatmap(gt, columns="Horsepower", hue="positive", kind="sequential")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Finalize and render
finalize(gt, path="table.png")
