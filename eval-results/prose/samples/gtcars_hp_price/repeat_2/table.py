import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Keep only the columns we need: model, hp, and msrp
df = df[["model", "hp", "msrp"]].copy()

# Ensure columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Step 2: Organize columns
# model is the stub (row identifier)
# hp and msrp are the measures to display

# Step 3: Big Color - both measures qualify (≥5 rows, ordered numeric)
# Horsepower appears first in request → primary (Blues)
# Price appears second → secondary (Greens per fallback ladder)
hp_cols = ["hp"]
msrp_cols = ["msrp"]

hp_lo = float(np.nanmin(df[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df[hp_cols].to_numpy()))

msrp_lo = float(np.nanmin(df[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(df[msrp_cols].to_numpy()))

# Step 4: Build the table with light heading band (since we have Big Color)
gt = (
    GT(df, rowname_col="model")
    # Step 2: Format columns
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", currency="USD")
    # Step 3: Data color (Big Color)
    # Primary: horsepower with Blues
    .data_color(
        columns="hp",
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Secondary: price with Greens (fallback for second neutral measure)
    .data_color(
        columns="msrp",
        palette="Greens",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (pale blue for Blues hue per grey-budget rule)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 6: Titles & annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance and market positioning of high-performance vehicles",
    )
    .tab_source_note("Data represents base model specifications and MSRP.")
)

# Render to PNG
gt.gtsave("table.png")
