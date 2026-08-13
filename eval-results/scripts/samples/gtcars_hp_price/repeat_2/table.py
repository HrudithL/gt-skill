import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create composite identifier for readability (mfr + model)
df["car"] = df["mfr"] + " " + df["model"]

# Select columns and drop duplicates/extras
df_display = df[["car", "hp", "msrp"]].copy()

# Step 2: Organize columns
# Stub will be 'car' (composite mfr + model)
# Hero measure: msrp (price is the natural financial hero per small_color.md)
# Secondary measure: hp (stays plain per redundancy check)

# Step 3: Determine Big Color
# Only msrp gets colored (column_gradient_fill for ordered magnitude)
# hp stays plain
cols_to_color = ["msrp"]
lo = float(np.nanmin(df_display[cols_to_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_to_color].to_numpy()))

# Step 4 & 5 & 6: Build the table with heading band, color, polish, and annotations
gt = (
    GT(df_display, rowname_col="car")
    # Formatting
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
    # Big Color: msrp gradient fill
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Small Color: borders (a) + column label bottom rule
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Frame borders (all four sides)
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
        # Compact layout padding
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Apply striping via helper
gt = stripe(gt)

# Apply stub tint via helper
gt = stub_tint(gt)

# Apply heading band via helper (Step 4)
gt = band(gt)

# Size columns to content
gt = gt.cols_width(cases={"car": "180px", "hp": "100px", "msrp": "130px"})

# Titles and annotations (Step 6)
gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle="Performance and market value across luxury vehicles",
)

# Add caption and source for ≥5 rows (two separate calls)
gt = gt.tab_source_note("Data: gtcars.csv")

# Step 7: Render with proper expand/zoom
finalize(gt, "table.png", expand=15, zoom=2.0)
