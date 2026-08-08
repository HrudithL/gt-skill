import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select and organize columns: mfr (stub), model, hp, msrp
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Step 2: Organize columns with stub
gt = GT(df_display, rowname_col="Manufacturer")

# Step 3: Big Color - both measures qualify and are colored
# Horsepower (primary) → Blues, Price (secondary) → Greens
hp_cols = ["Horsepower"]
price_cols = ["Price"]

hp_lo = float(np.nanmin(df_display[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df_display[hp_cols].to_numpy()))
price_lo = float(np.nanmin(df_display[price_cols].to_numpy()))
price_hi = float(np.nanmax(df_display[price_cols].to_numpy()))

gt = (
    gt
    .fmt_number(columns=hp_cols, decimals=0)
    .fmt_currency(columns=price_cols, decimals=0)
    .data_color(
        columns=hp_cols,
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=price_cols,
        palette="Greens",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band - LIGHT band with washed-DA tints
# Blues table stub → pale blue #EAF0F6
gt = (
    gt
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# Step 5: Small Color polish
# (a) Cell borders - hairline between rows
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# (c) Row striping (≥10 rows and not fully covered by Big Color)
gt = (
    gt
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
)

# (d) Stub tint - harmonize to pale blue (washed-DA tint for Blues table)
gt = (
    gt
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
)

# Frame - boxed border on all sides
gt = (
    gt
    .tab_options(
        table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
        table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
    )
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="GT Cars",
        subtitle="Horsepower and Price"
    )
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Render to PNG
gt.gtsave("table.png", expand=15)
