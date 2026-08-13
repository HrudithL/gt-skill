import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top = df.nlargest(10, "msrp").copy()

# Create display columns
df_top["drivetrain_trsmn"] = df_top["drivetrain"].str.upper() + " · " + df_top["trsmn"]
df_top["car_label"] = df_top["mfr"] + " " + df_top["model"] + " (" + df_top["year"].astype(str) + ")"

# Sort by country, then by price descending within country
df_top = df_top.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Prepare display dataframe
display_df = df_top[["car_label", "ctry_origin", "drivetrain_trsmn", "msrp"]].copy()
display_df.columns = ["Car", "Country", "Drivetrain / Transmission", "MSRP"]

# Step 2: Organize columns and determine grouping
# Using country as groupname_col for the grouping trigger (PP-1)
gt = GT(
    display_df,
    rowname_col="Car",
    groupname_col="Country"
)

# Step 3: Apply Big Color - MSRP is an ordered magnitude (neutral = price)
# Compute domain for MSRP
msrp_col = ["MSRP"]
lo = float(np.nanmin(display_df[msrp_col].to_numpy()))
hi = float(np.nanmax(display_df[msrp_col].to_numpy()))

gt = gt.fmt_currency(columns=["MSRP"], currency="USD", decimals=0)
gt = heatmap(
    gt,
    "MSRP",
    kind="sequential",
    hue="neutral",
    domain=[lo, hi]
)

# Step 4: Apply heading band (fixed navy band)
gt = band(gt)

# Step 5: Apply small color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Step 6: Add titles and annotations
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by Country of Origin"
)

gt = gt.tab_source_note(
    "MSRP represents manufacturer's suggested retail price in USD"
)

gt = gt.tab_source_note(
    "Data source: gtcars.csv"
)

# Optional: Compact layout for consistency
gt = gt.cols_width(
    cases={
        "Car": "280px",
        "Drivetrain / Transmission": "160px",
        "MSRP": "140px"
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

# Step 7: Render
finalize(gt, "table.png")
