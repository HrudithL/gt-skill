import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import heatmap, band, frame, finalize, hairlines, stripe, stub_tint, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create composite identifier: manufacturer + model
df["car"] = df["mfr"] + " " + df["model"]

# Get top 10 by MSRP
df = df.nlargest(10, "msrp").copy()

# Create a clean dataframe with desired columns
df_clean = df[["car", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()
df_clean.columns = ["Car", "Country", "Price", "Drivetrain", "Transmission"]

# Sort by country then by price descending
df_clean = df_clean.sort_values(["Country", "Price"], ascending=[True, False]).reset_index(drop=True)

# Build the table - Step 2: Organize columns with grouping
gt = GT(df_clean, rowname_col="Car", groupname_col="Country")

# Step 3: Big Color - MSRP is ordered magnitude, use Blues for price/money
gt = heatmap(gt, columns="Price", kind="sequential", hue="neutral")

# Step 5: Small Color polish checklist
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Format the columns
gt = (
    gt
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_options(
        column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
        column_labels_border_bottom_width="2px",
        row_striping_background_color=PALETTE["neutral"]["row_stripe"],
        heading_padding="12px",
        heading_padding_horizontal="12px",
        column_labels_padding="8px",
        column_labels_padding_horizontal="8px",
        data_row_padding="8px",
        data_row_padding_horizontal="8px",
        source_notes_padding="8px",
    )
)

# Step 4: Heading band (navy branding)
gt = band(gt)

# Step 6: Titles and annotations (two separate source note calls)
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin",
    )
    .tab_source_note(
        source_note="Price comparison displays MSRP for base models, showing premium vehicle pricing by country of origin and performance specifications."
    )
    .tab_source_note(
        source_note="Data source: gtcars.csv"
    )
)

# Set column widths for compact layout
gt = gt.cols_width(cases={
    "Car": "180px",
    "Country": "120px",
    "Price": "120px",
    "Drivetrain": "110px",
    "Transmission": "120px",
})

# Step 7: Render with proper expansion and zoom
finalize(gt)
