import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Load data
df = pd.read_csv("gtcars.csv")

# Step 1: Clean data
# The data is clean: hp and msrp are already numeric floats
# Select and rename columns for display
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Step 2: Organize columns
# Stub: Manufacturer+Model as a combined identifier
df_display["Car"] = df_display["Manufacturer"] + " " + df_display["Model"]
df_display = df_display[["Car", "Horsepower", "Price"]]

# Step 3: Big Color — Price (msrp) is ordered magnitude, ≥5 rows
# Palette: Blues (neutral magnitude — money/price)
# Domain: data-driven min/max
cols_color = ["Price"]
lo = float(np.nanmin(df_display[cols_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_color].to_numpy()))

# Step 4 & 5: Build the table with all formatting
gt = (
    GT(df_display, rowname_col="Car")
    # Formatting (Step 5e)
    .fmt_number(columns="Horsepower", decimals=0, use_seps=True)
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .sub_missing(columns=["Horsepower", "Price"], missing_text="—")
    # Big Color — Price gradient (Step 3)
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Cell borders (Step 5a) and row striping (Step 5c)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
    )
    # Stub tint (Step 5d) — light grey
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Heading band — Light band since Big Color present (Step 4)
    # Washed Navy tint to match Blues palette
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
    )
    # Frame borders (Step 5 global)
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
    # Titles and annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications and MSRP by manufacturer",
    )
    .tab_source_note("Data includes 2014-2017 grand-touring and high-performance vehicles")
)

# Render
gt.gtsave("table.png", expand=15, zoom=2.0)
