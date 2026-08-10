import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band,
    heatmap, stub_tint, group_emphasis, humanize_labels
)

# Read the data and sort by MSRP to get top 10
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Create a display column combining manufacturer and model
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Format transmission for readability
def format_transmission(trsmn):
    """Clean up transmission codes."""
    if pd.isna(trsmn):
        return "—"
    trsmn_str = str(trsmn).lower()
    # Map common transmission codes
    mapping = {
        "7a": "7-Speed Automatic",
        "6a": "6-Speed Automatic",
        "8a": "8-Speed Automatic",
        "8am": "8-Speed Automatic",
        "9a": "9-Speed Automatic",
        "7m": "7-Speed Manual",
        "6m": "6-Speed Manual",
        "6am": "6-Speed Automatic",
        "7am": "7-Speed Automatic",
        "m": "Manual",
        "a": "Automatic",
    }
    return mapping.get(trsmn_str, trsmn_str)

# Format drivetrain
def format_drivetrain(dt):
    """Clean up drivetrain codes."""
    if pd.isna(dt):
        return "—"
    dt_str = str(dt).lower()
    mapping = {
        "rwd": "RWD",
        "awd": "AWD",
        "fwd": "FWD",
    }
    return mapping.get(dt_str, dt_str.upper())

top_10["transmission"] = top_10["trsmn"].apply(format_transmission)
top_10["drivetrain"] = top_10["drivetrain"].apply(format_drivetrain)

# Select and rename columns
table_data = top_10[[
    "car",
    "ctry_origin",
    "msrp",
    "drivetrain",
    "transmission"
]].copy()

table_data.columns = [
    "car",
    "country",
    "msrp",
    "drivetrain",
    "transmission"
]

# Sort by country and MSRP
table_data = table_data.sort_values(["country", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create GT table with grouping
gt = (
    GT(table_data, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car")
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    table_data,
    overrides={
        "msrp": "MSRP",
        "drivetrain": "Drivetrain",
        "transmission": "Transmission",
        "country": "Country",
    }
)

# Apply the sequential heatmap to MSRP (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Styling
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source note and finalize
gt = (
    gt.tab_source_note(source_note="Source: gtcars.csv dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
