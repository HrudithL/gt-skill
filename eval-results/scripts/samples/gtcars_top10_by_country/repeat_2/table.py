import numpy as np
import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import (
    PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
)

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp").copy()

# Create a readable display version with manufacturer and model combined
top10["car"] = top10["mfr"] + " " + top10["model"]

# Sort by country then MSRP descending for clean grouping
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Select and rename columns for display
display_df = top10[["car", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()
display_df.columns = ["Car", "Country", "MSRP", "Drivetrain", "Transmission"]

# Step 2: Organize columns with grouping
gt = GT(display_df, groupname_col="Country", rowname_col="Car")

# Step 3: Big Color — MSRP is a neutral magnitude measure, color with Blues
cols_to_color = ["MSRP"]
gt = heatmap(gt, columns=cols_to_color, kind="sequential", hue="neutral")

# Step 4: Heading band — has Big Color, so use light band with Navy
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color — the fixed checklist

# (a) Cell borders — light hairline between rows + stronger structural rule for groups
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
    row_group_border_top_color=PALETTE["neutral"]["structural_rule"],
    row_group_border_bottom_color=PALETTE["neutral"]["structural_rule"],
)

# Row-group styling — background + bold + padding
gt = gt.tab_options(
    row_group_background_color=PALETTE["washed"]["navy"],
    row_group_font_weight="bold",
    row_group_padding="6px",
)

# Frame — boxed enclosing border on all sides
gt = frame(gt)

# (c) Row striping — ≥10 rows, striped unless fully filled by Big Color
gt = stripe(gt)

# (d) Stub tint — separate row labels with washed Navy tint (to match band)
gt = stub_tint(gt, hue="navy")

# (e) Formatting per column
gt = gt.fmt_currency(columns=["MSRP"], decimals=0, use_seps=True)
gt = gt.sub_missing(columns=["MSRP", "Drivetrain", "Transmission"], missing_text="—")

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by country of origin with drivetrain and transmission details"
)
gt = gt.tab_source_note(
    "Data source: gtcars.csv | Prices in USD"
)

# Stub head for the car names
gt = gt.tab_stubhead(label="Vehicle")

# Step 7: Render
finalize(gt)
