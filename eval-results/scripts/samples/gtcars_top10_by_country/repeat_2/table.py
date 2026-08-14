import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Data cleaning and preparation
df = pd.read_csv("gtcars.csv")

# Create a composite stub identifier (manufacturer + model)
df["car"] = df["mfr"] + " " + df["model"]

# Ensure numeric columns are properly typed
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Get top 10 most expensive cars
df_top10 = df.nlargest(10, "msrp").copy()

# Sort by country and then by price descending for better readability within groups
df_top10 = df_top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and rename columns for display
df_display = df_top10[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df_display.columns = ["Car", "Country", "Drivetrain", "Transmission", "MSRP"]

# Step 2: Build the table with grouping and stub
gt = GT(df_display, rowname_col="Car", groupname_col="Country")

# Step 3: Apply Big Color - MSRP gets a sequential gradient (neutral magnitude → Blues)
gt = heatmap(gt, columns="MSRP", kind="sequential", hue="neutral")

# Step 4: Heading band with fixed navy and white labels
gt = band(gt)

# Step 5: Small Color polish checklist
# (a) Cell borders - hairlines and structural rules
gt = hairlines(gt)

# Row-group emphasis: bold + structural rule (no fill)
gt = gt.tab_options(
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# (c) Row striping
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt)

# (e) Formatting per column
gt = gt.fmt_currency(columns="MSRP", currency="USD", decimals=0)
gt = gt.sub_missing(columns=["Drivetrain", "Transmission", "MSRP"], missing_text="—")

# (g) Compact layout
gt = gt.cols_width(cases={"Car": "180px", "Country": "140px", "Drivetrain": "100px", "Transmission": "110px", "MSRP": "130px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by Country of Origin"
)

# Footer: analytical caption + source note (two separate calls)
gt = gt.tab_source_note(
    source_note="Data shows the 10 most expensive GT automobiles, including drivetrain and transmission specifications."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv"
)

# Step 7: Frame and finalize
gt = frame(gt)
finalize(gt, "table.png", zoom=2, expand=10)
