import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels, group_emphasis
)

# Read and filter data
df = pd.read_csv("./gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by price (descending) for visual consistency
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create a display name combining manufacturer and model
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Clean up transmission codes for readability
def decode_transmission(code):
    """Decode transmission codes like 7a -> 7-Speed Auto"""
    if pd.isna(code):
        return "—"
    code_str = str(code)
    if code_str.endswith("a"):
        return f"{code_str[:-1]}-Speed Auto"
    elif code_str.endswith("m"):
        return f"{code_str[:-1]}-Speed Manual"
    elif code_str.endswith("am"):
        return f"{code_str[:-2]}-Speed Auto/Manual"
    elif code_str.endswith("dd"):
        return "Direct Drive"
    return code_str

top_10["transmission"] = top_10["trsmn"].apply(decode_transmission)

# Clean up drivetrain
def decode_drivetrain(code):
    """Decode drivetrain codes"""
    mapping = {"rwd": "RWD", "awd": "AWD", "fwd": "FWD"}
    return mapping.get(str(code).lower(), code)

top_10["drivetrain_label"] = top_10["drivetrain"].apply(decode_drivetrain)

# Select and order columns for display
display_df = top_10[["car", "ctry_origin", "drivetrain_label", "transmission", "msrp"]].copy()
display_df.columns = ["car", "country", "drivetrain", "transmission", "msrp"]

# Build the table
gt = GT(
    display_df,
    rowname_col="car",
    groupname_col="country"
)

gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle=md("Ranked by MSRP, grouped by country of origin — drivetrain and transmission details")
)

# Format MSRP as currency
gt = gt.fmt_currency(columns="msrp", decimals=0, currency="USD")

# Humanize labels
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "drivetrain": "Drivetrain",
        "transmission": "Transmission",
        "msrp": "MSRP"
    }
)

# Column widths
gt = gt.cols_width(
    cases={
        "car": "220px",
        "drivetrain": "100px",
        "transmission": "140px",
        "msrp": "130px",
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

# Heatmap for MSRP (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Heading band
gt = band(gt, hue="navy")

# Small-color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Source notes
gt = gt.tab_source_note(
    source_note="Top 10 cars ranked by MSRP in descending order."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv."
)

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Render
finalize(gt, path="table.png")
