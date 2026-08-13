import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, group_emphasis, humanize_labels
)

# Load the data
df = pd.read_csv("gtcars.csv")

# Select top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()

# Create a display-friendly car identifier
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Sort by country, then by price descending for better grouping
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Build the GT table
gt = (
    GT(top_10, rowname_col="car", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Premium sports and luxury vehicles ranked by MSRP, grouped by country of origin")
    )
    .tab_stubhead(label="Vehicle")
    .cols_hide(columns=["mfr", "model"])
    .fmt_currency(columns="msrp", decimals=0)
    .fmt_integer(columns="year")
)

# Humanize column labels with overrides for clarity
gt = humanize_labels(
    gt,
    top_10,
    overrides={
        "year": "Year",
        "drivetrain": "Drivetrain",
        "trsmn": "Transmission",
        "ctry_origin": "Country",
        "msrp": "Price (USD)"
    }
)

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "180px",
        "year": "70px",
        "drivetrain": "100px",
        "trsmn": "110px",
        "msrp": "130px",
    }
)

# Apply padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Color the price column (sequential heatmap for the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply house formatting
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Top 10 vehicles ranked by manufacturer suggested retail price (MSRP)."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars dataset."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and render
finalize(gt, path="table.png")
