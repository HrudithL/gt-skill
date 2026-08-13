import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("./gtcars.csv")

# Select relevant columns: manufacturer/model (stub), horsepower, and price
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create a display name combining manufacturer and model
df["car_name"] = df["mfr"] + " " + df["model"]
df = df[["car_name", "hp", "msrp"]]

# Rename columns for display
df = df.rename(columns={
    "car_name": "Car",
    "hp": "Horsepower",
    "msrp": "Price"
})

# Sort by price descending
df = df.sort_values("Price", ascending=False).reset_index(drop=True)

# Step 2: Organize columns with stub
gt = GT(df, rowname_col="Car")

# Step 3: Big Color - only MSRP (price) gets the fill
# Per small_color.md, hp and price are redundant dimensions (both proxies for "impressive")
# Price is the financial hero, so only it gets colored
cols_price = ["Price"]
lo = float(np.nanmin(df[cols_price].to_numpy()))
hi = float(np.nanmax(df[cols_price].to_numpy()))

# Step 4: Heading band (dark navy, fixed branding)
gt = (
    gt.tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="High-performance vehicles with detailed specifications"
    )
    .tab_options(
        # Heading band - fixed branding colors
        heading_background_color="#08306B",
    )
)

# Step 5: Small Color polish - comprehensive checklist

# (a) Cell borders - hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    row_striping_background_color="#F6F6F6",
)

# (c) Row striping - applies by default
gt = gt.opt_row_striping()

# (d) Stub tint - fixed pale-blue
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# (e) Formatting per column type
# Horsepower as plain number with 0 decimals
gt = gt.fmt_number(
    columns=["Horsepower"],
    decimals=0,
    use_seps=True,
)

# Price as currency (USD, whole dollars)
gt = gt.fmt_currency(
    columns=["Price"],
    currency="USD",
    decimals=0,
)

# Apply data_color to Price column only (Blues palette for neutral magnitude)
gt = gt.data_color(
    columns=["Price"],
    palette="Blues",
    domain=[lo, hi],
    truncate=False,
    na_color="#808080",
)

# (f) Titles & annotations - two footer notes
gt = (
    gt.tab_source_note(
        source_note="Price is the primary measure displayed with color gradient, as it represents the financial value. Horsepower is shown as a reference measure but not colored, as both metrics are proxies for vehicle performance."
    )
    .tab_source_note(
        source_note="Source: GT Cars dataset (gtcars.csv)"
    )
)

# Frame - boxed border on all sides
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

# Compact layout - column widths and padding
gt = gt.cols_width(cases={
    "Horsepower": "120px",
    "Price": "140px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Render to PNG
gt.gtsave("table.png", expand=15, zoom=2.0)
print("Table rendered successfully to table.png")
