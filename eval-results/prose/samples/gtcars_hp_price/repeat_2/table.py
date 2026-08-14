import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create a car identifier by combining manufacturer and model
df["car"] = df["mfr"] + " " + df["model"]

# Select and organize columns for the table
display_df = df[["car", "hp", "msrp"]].copy()
display_df = display_df.reset_index(drop=True)

# Step 2: Organize columns
# hp stays as integer, msrp as float
display_df["hp"] = display_df["hp"].astype(int)
display_df["msrp"] = display_df["msrp"].astype(float)

# Step 3: Compute domain for msrp (the colored measure)
msrp_cols = ["msrp"]
msrp_lo = float(np.nanmin(display_df[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(display_df[msrp_cols].to_numpy()))

# Build the table
gt = (
    GT(display_df, rowname_col="car")
    # Format columns
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0, use_seps=True)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Big Color: msrp gradient (Blues for neutral magnitude)
    # hp stays plain (redundancy: both rough proxies for "impressive car")
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (navy, white text)
    .tab_options(
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Column-label text: white (explicit pin)
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5: Small Color polish
    # (a) Cell borders / hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (body has colored + plain columns, so stripes apply)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame
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
    # Compact layout padding
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Column widths
    .cols_width(cases={"car": "200px", "hp": "100px", "msrp": "120px"})
    # Step 6: Titles & annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A collection of performance and luxury vehicles",
    )
    .tab_source_note(
        source_note="Price represents manufacturer's suggested retail price (MSRP); horsepower is the primary power output specification."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
