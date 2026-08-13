import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("gtcars.csv")

# Create a composite car identifier from mfr + model for the stub
df["car"] = df["mfr"] + " " + df["model"]

# Build the GT table with cars as the stub
gt = GT(
    df[["car", "hp", "msrp"]],
    rowname_col="car"
)

gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle=md("High-performance vehicles by manufacturer with engine power and MSRP")
)

gt = gt.tab_stubhead(label="Car")

# Format columns: hp as integer, msrp as currency
gt = gt.fmt_integer(columns="hp")
gt = gt.fmt_currency(columns="msrp", decimals=0)

# Humanize labels
gt = humanize_labels(gt, df[["car", "hp", "msrp"]])

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "200px",
        "hp": "100px",
        "msrp": "120px",
    }
)

# Set padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap to MSRP as the hero measure (price/financial magnitude)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply band with navy branding
gt = band(gt, hue="navy")

# Apply striping (since not all columns are heatmapped)
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue="navy")

# Apply hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Add source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Price (MSRP) colored by value as a financial magnitude."
)
gt = gt.tab_source_note(
    source_note="Source: provided gtcars dataset."
)

# Finalize and save
finalize(gt, path="table.png")
