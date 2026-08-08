import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe

# Load and prepare data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars overall, sorted by price descending
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by msrp descending within each country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a readable car name
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Select and order columns
top_10 = top_10[["ctry_origin", "car", "year", "drivetrain", "trsmn", "msrp"]]

gt = (
    GT(top_10, groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin, showing drivetrain and transmission details",
    )
    .cols_label(
        ctry_origin="Country",
        car="Car",
        year="Year",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        msrp="MSRP",
    )
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["year"], use_seps=False)
    .cols_align(align="left", columns=["car", "drivetrain", "trsmn"])
    .cols_align(align="right", columns=["year", "msrp"])
    .tab_source_note(source_note="Source: gtcars dataset (Posit / great_tables sample data).")
)

# Apply Big Color (MSRP as sequential Blues)
gt = heatmap(gt, columns="msrp", kind="sequential", hue="neutral")

# Apply light heading band (since we have Big Color)
gt = band(gt, shade="light", hue="navy")

# Apply row striping (>=10 rows and body not fully filled)
gt = stripe(gt)

# Apply frame and finalize
gt = frame(gt)
gt = finalize(gt)
