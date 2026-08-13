import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("gtcars.csv")
df = df[["mfr", "model", "hp", "msrp"]].copy()
df = df.dropna(subset=["hp", "msrp"])

# Create composite stub label
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]]

# Step 2: Organize columns
cols_measure = ["hp", "msrp"]
cols = cols_measure

# Compute domains for color
lo_msrp = float(np.nanmin(df[["msrp"]].to_numpy()))
hi_msrp = float(np.nanmax(df[["msrp"]].to_numpy()))

# Step 3 & 4 & 5: Build the table
gt = (
    GT(df, rowname_col="car")
    # Column labels
    .cols_label(hp="Horsepower", msrp="Price ($)")
    # Column widths
    .cols_width(cases={"hp": "100px", "msrp": "100px"})
    # Formatting
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0, currency="USD")
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Big Color: only msrp is colored (hp is redundant)
    .data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[lo_msrp, hi_msrp],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="High-performance vehicles ranked by MSRP",
    )
    # Step 5: Small Color Polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Heading band (Step 4)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Padding (compact layout)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame borders
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
    # (f) Titles & annotations
    .tab_source_note(source_note="Horsepower and price are both proxies for overall car impressiveness, making them near-redundant dimensions. Price (MSRP) is the hero measure and is color-encoded; horsepower remains plain text.")
    .tab_source_note(source_note="Source: GT Cars dataset.")
)

gt.gtsave("table.png", expand=15)
