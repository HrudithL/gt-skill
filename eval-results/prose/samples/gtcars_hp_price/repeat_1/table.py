import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select only the columns we need and rename for clarity
df = df[["mfr", "model", "hp", "msrp"]].copy()
df.rename(columns={"mfr": "Manufacturer", "model": "Model", "hp": "Horsepower", "msrp": "Price"}, inplace=True)

# Create a combined identifier column for the stub
df["car"] = df["Manufacturer"] + " " + df["Model"]
df = df.drop(columns=["Manufacturer", "Model"])

# Ensure numeric columns are clean
df["Horsepower"] = pd.to_numeric(df["Horsepower"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

# Sort by horsepower for better readability
df = df.sort_values("Horsepower", ascending=False).reset_index(drop=True)

# Compute domains for the colored measures
hp_cols = ["Horsepower"]
price_cols = ["Price"]

hp_lo = float(np.nanmin(df[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(df[hp_cols].to_numpy()))

price_lo = float(np.nanmin(df[price_cols].to_numpy()))
price_hi = float(np.nanmax(df[price_cols].to_numpy()))

# Step 2: Organize columns with stub
# The "car" column will be the stub (rowname_col)

# Step 3: Big Color — two neutral measures
# Primary: Horsepower (Blues)
# Secondary: Price (Greens, per tie-breaker rule for two neutral measures)

gt = (
    GT(df, rowname_col="car")
    # Step 3: Add Big Color fills
    .data_color(
        columns="Horsepower",
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Price",
        palette="Greens",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 5: Format numbers
    .fmt_number(columns="Horsepower", decimals=0, use_seps=True)
    .fmt_currency(columns="Price", decimals=0, use_seps=True)
    .sub_missing(columns=["Horsepower", "Price"], missing_text="—")
    # Step 4: Light heading band (because we have Big Color)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # pale blue (Blues table)
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),  # pale blue to harmonize with Blues
        locations=loc.stub(),
    )
    # Step 5: Cell borders (hairlines + structural)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5: Row striping (≥10 rows)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Frame border
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
    # Step 6: Titles & annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A selection of high-performance vehicles sorted by horsepower",
    )
    .tab_source_note(
        source_note="Data source: gtcars.csv",
    )
)

# Render
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
