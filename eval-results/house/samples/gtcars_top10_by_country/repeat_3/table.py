import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, group_emphasis, humanize_labels

# Load data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp").copy()

# Create car identifier (mfr + model)
top10["car"] = top10["mfr"] + " " + top10["model"]

# Sort by country, then by price descending for better grouping
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and rename columns for display
display_df = top10[[
    "car",
    "ctry_origin",
    "year",
    "drivetrain",
    "trsmn",
    "msrp"
]].copy()

display_df.columns = ["Car", "Country", "Year", "Drivetrain", "Transmission", "MSRP"]

# Create GT table with country as group
gt = GT(
    display_df,
    rowname_col="Car",
    groupname_col="Country"
)

# Format MSRP as currency
gt = gt.fmt_currency(columns="MSRP", decimals=0)

# Apply grouping emphasis
gt = group_emphasis(gt)

# Add title and subtitle
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by Country of Origin"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by MSRP (Manufacturer's Suggested Retail Price); includes drivetrain and transmission details."
)
gt = gt.tab_source_note(
    source_note="Source: provided gtcars dataset."
)

# Color the MSRP column with sequential heatmap
gt = heatmap(gt, "MSRP", kind="sequential", hue="neutral")

# Apply frame and styling
gt = frame(gt)
gt = hairlines(gt)
gt = band(gt, hue="navy")

# Apply striping
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue="navy")

# Finalize and render
finalize(gt, path="table.png")
