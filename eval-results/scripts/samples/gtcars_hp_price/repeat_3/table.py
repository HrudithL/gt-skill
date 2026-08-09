import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize

df = pd.read_csv("gtcars.csv")

# Step 1: Clean and prepare data
# Select and rename columns for clarity
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["manufacturer", "model", "hp", "price"]

# Combine manufacturer and model for the stub
df_display["car"] = df_display["manufacturer"] + " " + df_display["model"]
df_display = df_display[["car", "hp", "price"]]

# Ensure numeric types are correct
df_display["hp"] = pd.to_numeric(df_display["hp"], errors="coerce")
df_display["price"] = pd.to_numeric(df_display["price"], errors="coerce")

# Sort by price descending for better readability
df_display = df_display.sort_values("price", ascending=False).reset_index(drop=True)

# Step 2: Organize columns with stub
gt = GT(df_display, rowname_col="car")

# Step 3: Big Color - two neutral magnitudes
# Price is primary (Blues), HP is secondary (Greens fallback)
hp_lo = float(np.nanmin(df_display[["hp"]].to_numpy()))
hp_hi = float(np.nanmax(df_display[["hp"]].to_numpy()))
price_lo = float(np.nanmin(df_display[["price"]].to_numpy()))
price_hi = float(np.nanmax(df_display[["price"]].to_numpy()))

gt = (
    gt
    .fmt_integer(columns="hp", use_seps=True)
    .fmt_currency(columns="price", currency="USD", decimals=0, use_seps=True)
    .data_color(
        columns="price",
        palette="Blues",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="hp",
        palette="Greens",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band - light band with washed-DA tint (Blues → #EAF0F6)
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",
    column_labels_font_weight="bold",
)

# Step 5: Small Color polish checklist

# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (c) Row striping - enable since ≥10 rows and not fully filled
gt = gt.opt_row_striping()
gt = gt.tab_options(row_striping_background_color="#F6F6F6")

# (d) Stub tint - harmonize to washed-DA tint for Blues table
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# (e) Frame border and margin
gt = frame(gt)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="GT Performance Vehicles",
        subtitle="Horsepower and Market Price Comparison",
    )
    .tab_source_note(
        source_note="Source: gtcars dataset."
    )
)

# Step 7: Render
finalize(gt)
