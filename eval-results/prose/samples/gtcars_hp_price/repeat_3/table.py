import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("gtcars.csv")

# Verify necessary columns exist
assert "hp" in df.columns and "msrp" in df.columns, "Missing hp or msrp column"
assert len(df) >= 5, "Need at least 5 rows for gradient fill"

# Create a display column with manufacturer + model
df["car"] = df["mfr"] + " " + df["model"]

# Select and reorder columns for display
display_df = df[["car", "hp", "msrp"]].copy()

# Ensure numeric types
display_df["hp"] = pd.to_numeric(display_df["hp"], errors="coerce")
display_df["msrp"] = pd.to_numeric(display_df["msrp"], errors="coerce")

# Compute domains for data_color
hp_cols = ["hp"]
msrp_cols = ["msrp"]
hp_lo = float(np.nanmin(display_df[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(display_df[hp_cols].to_numpy()))
msrp_lo = float(np.nanmin(display_df[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(display_df[msrp_cols].to_numpy()))

# Step 2: Create GT object
gt = GT(display_df)

# Step 3: Big Color — horsepower (primary, Blues) and price (secondary, Greens)
gt = (
    gt.data_color(
        columns=["hp"],
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["msrp"],
        palette="Greens",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band — light Navy tint (washed-DA, no Big Color hue dominates)
# Apply column label options with light background and bottom rule
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small Color polish
# (a) Cell borders — hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Frame — boxed enclosing border
gt = gt.tab_options(
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
)

# (c) Row striping — 30 rows, body is fully filled by Big Color, so skip striping per gate

# (e) Formatting per column
gt = (
    gt.fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0, use_seps=True, currency="USD")
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="GT Cars Performance & Price",
        subtitle="Horsepower and MSRP for high-performance vehicles",
    )
    .tab_source_note(source_note="Data compiled from 30 GT sports cars spanning multiple manufacturers and model years.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
