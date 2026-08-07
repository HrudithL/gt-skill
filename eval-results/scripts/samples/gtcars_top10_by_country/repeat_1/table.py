import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Ensure MSRP is numeric
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Get top 10 by MSRP
df_top10 = df.nlargest(10, "msrp").copy()

# Create display columns
df_top10["car"] = df_top10["mfr"] + " " + df_top10["model"]

# Select and rename columns for display
display_cols = ["ctry_origin", "car", "drivetrain", "trsmn", "msrp"]
df_display = df_top10[display_cols].copy()
df_display.columns = ["Country", "Car", "Drivetrain", "Transmission", "MSRP"]

# Sort by country, then by MSRP descending within each country
df_display = df_display.sort_values(["Country", "MSRP"], ascending=[True, False]).reset_index(drop=True)

# Step 2: Calculate domain for Big Color
cols = ["MSRP"]
lo = float(np.nanmin(df_display[cols].to_numpy()))
hi = float(np.nanmax(df_display[cols].to_numpy()))

# Step 3 & 4 & 5: Build table with Big Color (Blues gradient) and Light band
gt = (
    GT(df_display, rowname_col="Car", groupname_col="Country")
    .fmt_currency(columns="MSRP", currency="USD", decimals=0)
    .data_color(
        columns="MSRP",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light band (Big Color present) with washed Navy tint
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Cell borders and striping
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
    )
    .opt_row_striping()
    # Titles and subtitle
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Organized by country of origin with drivetrain and transmission details"
    )
    # Frame and finalization
)

# Add subtle frame via borders
gt = gt.tab_style(
    style=style.borders(sides="all", color="#CCCCCC", weight="1px"),
    locations=loc.body(),
)

gt.gtsave("table.png")
