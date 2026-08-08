import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("gtcars.csv")

# Keep only the columns we need
df = df[["model", "mfr", "hp", "msrp"]].copy()

# Ensure numeric columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Step 2: Organize columns and determine Big Color
# Both hp and msrp qualify (≥5 rows, numeric magnitude)
# hp is primary (prompt mentions horsepower first), msrp is secondary
# By the tie-breaker rule for two neutral measures: hp → Blues, msrp → Greens

# Step 3: Compute domains for Big Color
hp_cols = ["hp"]
price_cols = ["msrp"]

hp_lo = float(np.nanmin(df[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df[hp_cols].to_numpy()))

price_lo = float(np.nanmin(df[price_cols].to_numpy()))
price_hi = float(np.nanmax(df[price_cols].to_numpy()))

# Step 4 & 5: Build the table with heading band (light, washed Navy), polish, and formatting
gt = (
    GT(df, rowname_col="model")
    # Step 5(a): Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5(c): Row striping (≥10 rows)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5(d): Stub tint (grey default)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Step 5(e): Format columns
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Step 3: Big Color - hp (Blues, primary)
    .data_color(
        columns=["hp"],
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 3: Big Color - msrp (Greens, secondary per tie-breaker)
    .data_color(
        columns=["msrp"],
        palette="Greens",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (light Navy tint, has Big Color)
    .tab_options(
        column_labels_background_color="#EAF0F6",
    )
    # Frame: light border on all sides
    .tab_options(
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
    # Step 6: Titles and annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Comparison of luxury and performance vehicles"
    )
    .tab_source_note(source_note="Source: provided GT cars dataset.")
)

# Render to PNG
gt.gtsave("table.png", expand=15)
