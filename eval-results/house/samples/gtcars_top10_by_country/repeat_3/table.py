import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, finalize, band, stub_tint, heatmap, group_emphasis, humanize_labels
)

# Read the data
gtcars = pd.read_csv("gtcars.csv")

# Get the top 10 most expensive cars
top10 = gtcars.nlargest(10, "msrp").copy()

# Sort by country and then by price (descending) for better grouping
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display-friendly version
display_data = top10[["mfr", "model", "year", "drivetrain", "trsmn", "msrp", "ctry_origin"]].copy()
display_data.columns = ["manufacturer", "model", "year", "drivetrain", "transmission", "msrp", "country"]

# Reorder columns for the table
display_data = display_data[["manufacturer", "model", "year", "drivetrain", "transmission", "msrp", "country"]]

# Build the table
gt = (
    GT(display_data, rowname_col="manufacturer", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Manufacturer")
    .fmt_currency(columns="msrp", decimals=0, currency="USD")
    .fmt_integer(columns="year")
)

# Apply humanize_labels with overrides
gt = humanize_labels(
    gt,
    display_data,
    overrides={"msrp": "MSRP (USD)"},
)

# Apply color to MSRP as the hero measure (sequential, neutral = Blues)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply styling
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source note and frame
gt = (
    gt.tab_source_note(source_note="Source: gtcars.csv dataset")
)

gt = frame(gt)
finalize(gt, path="table.png")
