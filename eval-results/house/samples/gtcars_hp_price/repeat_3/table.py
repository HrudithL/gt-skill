import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap
)

# Read the data
df = pd.read_csv("gtcars.csv")

# Select the relevant columns: manufacturer + model as stub, hp and price
df["car"] = df["mfr"] + " " + df["model"]
display_df = df[["car", "hp", "msrp"]].copy()
display_df = display_df.rename(columns={"hp": "horsepower", "msrp": "price"})

# Create the GT table
gt = (
    GT(display_df, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications and pricing"
    )
    .fmt_integer(columns="horsepower")
    .fmt_currency(columns="price", decimals=0)
    .cols_width(
        cases={
            "car": "200px",
            "horsepower": "120px",
            "price": "120px",
        }
    )
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Apply Big Color: price is the hero measure (neutral sequential Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Apply branding
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes and formatting
gt = (
    gt.tab_source_note(source_note="Price is the MSRP in USD.")
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
