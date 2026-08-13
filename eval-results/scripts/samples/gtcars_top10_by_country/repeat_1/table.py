import numpy as np
import pandas as pd
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, hairlines, band, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

# Step 1: Understand the data & clean
df = df[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df = df.sort_values("msrp", ascending=False).head(10).reset_index(drop=True)

# Create composite identifier: manufacturer + model
df["car"] = df["mfr"] + " " + df["model"]

# Step 2: Organize columns
df_display = df[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df_display = df_display.rename(columns={
    "ctry_origin": "country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "Price (USD)"
})

# Step 3 & 4: Build table with grouping, apply heading band
gt = (
    GT(df_display, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .fmt_currency(columns=["Price (USD)"], currency="USD", decimals=0)
)

# Step 3: Apply Big Color (heatmap on price)
gt = heatmap(gt, columns=["Price (USD)"], kind="sequential", hue="neutral")

# Step 4: Apply fixed heading band
gt = band(gt)

# Step 5: Small Color polish
gt = (
    hairlines(gt)
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        heading_padding="12px",
        column_labels_padding="10px",
        column_labels_padding_horizontal="8px",
        data_row_padding="8px",
        data_row_padding_horizontal="8px",
        source_notes_padding="10px",
    )
)

gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Step 6: Add annotations (two separate source notes)
gt = (
    gt.tab_source_note("Source: gtcars.csv. Price shown in MSRP (manufacturer suggested retail price) in USD.")
)

# Step 7: Render with proper gtsave parameters
finalize(gt)
