"""Top 10 most expensive GT cars grouped by country of origin."""

import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, group_emphasis, humanize_labels

# Read the data
df = pd.read_csv("gtcars.csv")

# Create a car identifier column (mfr + model)
df["car"] = df["mfr"] + " " + df["model"]

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].reset_index(drop=True)

# Sort by country, then by price descending within country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table
gt = (
    GT(top_10, rowname_col="car", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission details",
    )
    .tab_stubhead(label="Car")
    .fmt_currency(columns="msrp", decimals=0)
)

# Humanize labels with overrides for clarity
gt = humanize_labels(
    gt,
    top_10,
    overrides={
        "ctry_origin": "Country",
        "drivetrain": "Drivetrain",
        "trsmn": "Transmission",
        "msrp": "Price (USD)",
    },
)

# Set column widths and padding
gt = gt.cols_width(
    cases={
        "car": "200px",
        "drivetrain": "110px",
        "trsmn": "110px",
        "msrp": "130px",
    }
)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap to the price column (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply styling: band, stripe, stub tint, group emphasis
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by MSRP (manufacturer suggested retail price) in descending order."
)
gt = gt.tab_source_note(source_note="Source: gtcars.csv dataset.")

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
