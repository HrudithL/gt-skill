import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Clean data
df = pd.read_csv("gtcars.csv")

# Create a readable stub combining manufacturer and model
df["car"] = df["mfr"] + " " + df["model"]

# Select and rename columns
df = df[["car", "hp", "msrp"]].copy()
df.columns = ["Car", "Horsepower", "Price"]

# Ensure numeric columns
df["Horsepower"] = pd.to_numeric(df["Horsepower"], errors="coerce")
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

# Step 2: Organize columns + Step 3: Big Color (price heatmap)
# Compute domain for Price (msrp) heatmap
price_cols = ["Price"]
price_lo = float(np.nanmin(df[price_cols].to_numpy()))
price_hi = float(np.nanmax(df[price_cols].to_numpy()))

# Step 4: Heading band + Step 5: Small Color polish
gt = (
    GT(df, rowname_col="Car")
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Formatting per column
    .fmt_number(columns="Horsepower", decimals=0, use_seps=True)
    .fmt_currency(columns="Price", decimals=0, use_seps=True)
    # Step 3: Big Color — Price heatmap (hp stays plain per redundancy check)
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    # Heading band (Step 4) — navy band with white text
    .tab_header(
        title="GT Cars",
        subtitle="Horsepower and Price",
    )
    # Column width sizing (compact layout)
    .cols_width(cases={
        "Horsepower": "120px",
        "Price": "140px",
    })
    # Padding (compact layout)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame border (all four sides)
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
    .tab_source_note(source_note="Price (MSRP) is colored to show relative cost; horsepower is displayed as a plain measure since both metrics serve the same narrative of vehicle capability and cost.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt.gtsave("table.png", expand=15)
