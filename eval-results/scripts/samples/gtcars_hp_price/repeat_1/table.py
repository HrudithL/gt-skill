import sys
sys.path.insert(0, "./.claude/skills/great-tables-ci/scripts")

import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and rename
df = df[["mfr", "model", "hp", "msrp"]].copy()
df = df.rename(columns={"mfr": "Manufacturer", "model": "Model", "hp": "Horsepower", "msrp": "Price ($)"})

# Create a display stub from manufacturer and model
df_display = df.copy()
df_display["Car"] = df_display["Manufacturer"] + " " + df_display["Model"]
df_display = df_display[["Car", "Horsepower", "Price ($)"]].reset_index(drop=True)

# Step 2: Organize columns
# Car is the stub, Horsepower and Price are measures

# Step 3: Big Color — two qualifying measures (hp and Price, both ordered numeric ≥5 rows)
# Primary: Horsepower (mentioned first)
# Secondary: Price
# Palette: Horsepower → Greens (measure-driven), Price → Blues (neutral magnitude/money)

# Compute domains
hp_cols = ["Horsepower"]
price_cols = ["Price ($)"]

hp_min = float(np.nanmin(df_display[hp_cols].to_numpy()))
hp_max = float(np.nanmax(df_display[hp_cols].to_numpy()))

price_min = float(np.nanmin(df_display[price_cols].to_numpy()))
price_max = float(np.nanmax(df_display[price_cols].to_numpy()))

# Step 4 & 5: Build the table with heading band and small-color polish
gt = (
    GT(df_display, rowname_col="Car")
    # Formatting
    .fmt_number(columns=["Horsepower"], decimals=0)
    .fmt_currency(columns=["Price ($)"], currency="USD", decimals=0)
    .sub_missing(columns=["Horsepower", "Price ($)"], missing_text="—")
    # Big Color: heatmap for both measures
    .data_color(
        columns="Horsepower",
        palette="Greens",
        domain=[hp_min, hp_max],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Price ($)",
        palette="Blues",
        domain=[price_min, price_max],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (light, since we have Big Color) — Navy hue
    .tab_options(
        column_labels_background_color="#EAF0F6",  # light Navy tint
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (≥10 rows AND not fully colored)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint (light Navy tint to harmonize with Big Color)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
)

# Apply frame
gt = frame(gt)

# Titles
gt = (
    gt.tab_header(
        title="GT Cars: Horsepower & Price",
        subtitle="Performance and value across premium sports cars",
    )
)

# Finalize (margin & zoom) — gtsave is called inside finalize
finalize(gt)
