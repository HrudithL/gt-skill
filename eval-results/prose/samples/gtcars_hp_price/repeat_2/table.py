import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Clean the data
df = pd.read_csv("gtcars.csv")

# Keep only relevant columns and create a readable identifier
df["car"] = df["mfr"] + " " + df["model"]
df_display = df[["car", "hp", "msrp"]].copy()
df_display.columns = ["car", "hp", "msrp"]

# Set car as index (will become stub)
df_display = df_display.set_index("car").reset_index()

# Step 2: Create the GT table with stub
gt = GT(df_display, rowname_col="car")

# Step 3: Apply Big Color — gradient fill for both horsepower and price
# Compute domains for each measure
hp_cols = ["hp"]
hp_lo = float(np.nanmin(df_display[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df_display[hp_cols].to_numpy()))

msrp_cols = ["msrp"]
msrp_lo = float(np.nanmin(df_display[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(df_display[msrp_cols].to_numpy()))

# Apply Big Color fills
gt = (
    gt
    # Horsepower: primary neutral measure → Blues
    .data_color(
        columns=hp_cols,
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Price: secondary neutral measure → Greens (per tie-breaker)
    .data_color(
        columns=msrp_cols,
        palette="Greens",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Light heading band (since Big Color is present)
# Use washed-DA tint matching the primary hue (Blues → pale-blue)
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",  # pale-blue washed tint for Blues
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small-Color polish checklist

# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# (c) Row striping (≥10 rows, not fully filled)
gt = gt.opt_row_striping()

# (d) Stub tint (use washed-DA tint to harmonize with Big Color)
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),  # pale-blue to match Blues theme
    locations=loc.stub(),
)

# (e) Formatting per column
gt = (
    gt
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0, use_seps=True)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Frame: light border on all sides + margin
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

# Add titles and captions
gt = (
    gt
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Comparative specifications across luxury and performance vehicles",
    )
    .tab_source_note(
        source_note="Data: gtcars.csv | Horsepower (Blues) and Price (Greens) gradients show relative magnitude.",
    )
)

# Render to PNG
gt.gtsave("table.png", expand=15)
print("✓ Table rendered to table.png")
