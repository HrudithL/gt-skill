import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

df = pd.read_csv("gtcars.csv")

# Create car identifier: mfr + model (composite stub grain)
df["car"] = df["mfr"] + " " + df["model"]

# Select relevant columns
df_table = df[["car", "hp", "msrp"]].copy()

# Rename for clarity
df_table = df_table.rename(columns={"hp": "horsepower", "msrp": "price"})

gt = GT(df_table, rowname_col="car")
gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle=md("High-performance automobiles with engine power and market value")
)

# Format columns
gt = gt.fmt_number(columns="horsepower", decimals=0)
gt = gt.fmt_currency(columns="price", decimals=0)

# Humanize labels
gt = humanize_labels(gt, df_table)

# Column widths
gt = gt.cols_width(cases={
    "horsepower": "120px",
    "price": "120px",
})

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Color: price is the sequential hero measure (neutral magnitude → Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Small-color polish
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Price is the manufacturer's suggested retail price (MSRP) in USD."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars dataset."
)

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
