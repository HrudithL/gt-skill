import pandas as pd
from great_tables import GT, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, group_emphasis, humanize_labels

# Read the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")

# Sort by country and then by price descending
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create a display name for the car
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Select and reorder columns
display_df = top_10[["car", "ctry_origin", "year", "msrp", "drivetrain", "trsmn"]].copy()

# Create the GT table
gt = GT(
    display_df,
    rowname_col="car",
    groupname_col="ctry_origin"
)

# Header
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by country of origin, sorted by price"
)

# Stub head
gt = gt.tab_stubhead(label="Car Model")

# Format columns
gt = (
    gt.fmt_integer(columns="year")
    .fmt_currency(columns="msrp", decimals=0)
)

# Humanize labels
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "ctry_origin": "Country",
        "msrp": "Price (USD)",
        "drivetrain": "Drivetrain",
        "trsmn": "Transmission"
    }
)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "car": "180px",
        "ctry_origin": "130px",
        "year": "80px",
        "msrp": "130px",
        "drivetrain": "100px",
        "trsmn": "110px",
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

# Apply heatmap to MSRP (the hero measure)
from house_table import heatmap
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply styling
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = band(gt, hue="navy")
gt = group_emphasis(gt)

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Top 10 ranked by MSRP (manufacturer's suggested retail price)."
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
