import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import band, frame, finalize, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df = df.nlargest(10, "msrp").copy()

# Create a display name combining manufacturer and model for better readability
df["car"] = df["mfr"] + " " + df["model"]

# Sort by country then by price descending for better grouping
df = df.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and order columns for display
display_df = df[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
display_df.columns = ["Car", "Country", "Drivetrain", "Transmission", "MSRP"]

# Compute domain for MSRP color gradient
msrp_col = ["MSRP"]
msrp_min = float(np.nanmin(display_df[msrp_col].to_numpy()))
msrp_max = float(np.nanmax(display_df[msrp_col].to_numpy()))

# Step 2 & 3: Build table with grouping and color
gt = (
    GT(display_df, rowname_col="Car", groupname_col="Country")
    .fmt_currency(columns=["MSRP"], decimals=0, use_seps=True)
    .data_color(
        columns=["MSRP"],
        palette="Blues",
        domain=[msrp_min, msrp_max],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# Apply band, stripe, stub tint, and frame
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Step 5: Cell borders and hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Step 5: Row group emphasis (stronger top border at group boundaries)
row_group_indices = []
current_country = None
for idx, country in enumerate(display_df["Country"]):
    if country != current_country:
        if current_country is not None:
            row_group_indices.append(idx)
        current_country = country

if row_group_indices:
    gt = gt.tab_style(
        style=style.borders(sides="top", color="#BDBDBD", weight="1.5px"),
        locations=loc.body(rows=row_group_indices),
    )

# Step 6: Titles and annotations
gt = (
    gt.tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Ordered by price within each country of origin",
    )
    .tab_source_note(
        source_note="MSRP shown in USD; prices reflect manufacturer's suggested retail price at time of data collection."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 5: Compact layout and padding
gt = (
    gt.cols_width(cases={"Car": "200px", "Drivetrain": "90px", "Transmission": "100px", "MSRP": "110px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 7: Render with frame
gt = frame(gt)
finalize(gt)
