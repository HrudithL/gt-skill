import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create stub label combining manufacturer and model for better readability
df["car"] = df["mfr"] + " " + df["model"]

# Select and reorder columns: stub + horsepower (plain) + price (colored)
df_display = df[["car", "hp", "msrp"]].copy()
df_display = df_display.head(30)  # Show first 30 cars for readability

# Step 2: Organize columns and create GT object with stub
gt = GT(df_display, rowname_col="car")

# Step 3: Apply Big Color to price (msrp) only — price is the financial hero
# Horsepower stays plain per the redundancy check
gt = heatmap(gt, columns="msrp", kind="sequential", hue="neutral")

# Step 4: Apply heading band (navy branding tier)
gt = band(gt)

# Step 5: Small Color polish checklist
# (a) Cell borders — hairlines between rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (c) Row striping
gt = stripe(gt)

# (d) Stub tint
gt = stub_tint(gt)

# (e) Formatting per column
gt = gt.fmt_number(columns="hp", decimals=0, use_seps=True)
gt = gt.fmt_currency(columns="msrp", decimals=0, use_seps=True)
gt = gt.sub_missing(columns=["hp", "msrp"], missing_text="—")

# Adjust column widths
gt = gt.cols_width(cases={"hp": "100px", "msrp": "120px"})

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Sample of high-performance vehicles"
    )
    .tab_source_note(source_note="Price is the colored measure; horsepower provides context.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Padding values
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 7: Frame and render
gt = frame(gt)
finalize(gt)
