import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

# Read the data
df = pd.read_csv("gtcars.csv")

# Create composite car identifier (mfr + model) and sort
df["car"] = df["mfr"] + " " + df["model"]
df = df.sort_values("hp", ascending=False).reset_index(drop=True)

# Select and rename columns for the table
display_df = df[["car", "hp", "msrp"]].copy()
display_df.columns = ["car", "horsepower", "price"]

# Build the table
gt = GT(display_df, rowname_col="car")
gt = gt.tab_header(
    title="GT Cars by Horsepower and Price",
    subtitle=md("High-performance vehicles ranked by horsepower with MSRP"),
)

# Format columns
gt = gt.fmt_integer(columns="horsepower")
gt = gt.fmt_currency(columns="price", decimals=0)

# Humanize labels (skip the car column which is already the stub)
gt = humanize_labels(gt, display_df, overrides={"horsepower": "Horsepower", "price": "Price"})

# Apply styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add heatmap for horsepower (the primary measure from the topic)
gt = heatmap(gt, "horsepower", kind="sequential", hue="neutral")

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "200px",
        "horsepower": "120px",
        "price": "140px",
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

# Add source notes
gt = gt.tab_source_note(
    source_note="Horsepower is the primary sorting measure; price is shown for reference."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv dataset."
)

# Apply final styling
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
