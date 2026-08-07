import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Keep only the columns we need: mfr, model, hp, msrp
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create a display column combining mfr and model
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].copy()

# Ensure numeric columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Remove rows with missing values
df = df.dropna()

# Step 2: Organize columns - car is the stub/identifier
# Step 3: Big Color - both hp and msrp qualify as ordered magnitudes (≥5 rows)
# Primary (hp, leftmost): Blues
# Secondary (msrp): Greens (fallback for second neutral magnitude)

# Compute domains for data_color
hp_cols = ["hp"]
msrp_cols = ["msrp"]

hp_lo = float(np.nanmin(df[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df[hp_cols].to_numpy()))

msrp_lo = float(np.nanmin(df[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(df[msrp_cols].to_numpy()))

# Step 4: Build table with light band (Big Color present)
gt = (
    GT(df, rowname_col="car")
    # Format columns
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
    # Step 3: Big Color - two colored measures
    .data_color(
        columns="hp",
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="msrp",
        palette="Greens",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (washed-DA tint, matching Blues hue)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # pale blue for Blues table
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Frame
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
    # (c) Row striping (≥10 rows and not fully filled)
    .opt_row_striping()
    # (d) Stub tint (grey default, or washed-DA if grey becomes monotonous)
    .tab_style(
        style=style.fill(color="#EAF0F6"),  # harmonize stub to pale blue (grey-budget rule)
        locations=loc.stub(),
    )
    # Column labels
    .tab_style(
        style=style.text(color="#000000"),  # dark text on light band
        locations=loc.column_labels(),
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table saved to table.png")
