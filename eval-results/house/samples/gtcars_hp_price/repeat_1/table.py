import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("gtcars.csv")

# Select and prepare columns
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create row identifier as composite of manufacturer and model
df["car"] = df["mfr"] + " " + df["model"]

# Remove the now-redundant mfr/model columns
df = df[["car", "hp", "msrp"]]

# Sort by horsepower descending for narrative interest
df = df.sort_values("msrp", ascending=False).reset_index(drop=True)

gt = (
    GT(df, rowname_col="car")
    .tab_header(
        title="GT Cars",
        subtitle=md("Horsepower and price by model"),
    )
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(gt, df)

# Column widths
gt = gt.cols_width(
    cases={
        "car": "200px",
        "hp": "100px",
        "msrp": "120px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply color to the hero measure (price)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Horsepower and MSRP are displayed for each model; sorted by price."
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
