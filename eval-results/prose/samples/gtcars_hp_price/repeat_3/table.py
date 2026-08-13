import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("./gtcars.csv")

# Keep only the columns we need: model (stub), hp, msrp
df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create a composite model identifier (mfr + model) for clarity
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].rename(columns={"car": "model"})

# Ensure numeric columns are floats
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Step 2: Organize columns and create GT
gt = GT(df, rowname_col="model")

# Step 3 & 4 & 5: Build the table with formatting, colors, and styling
# Heading band - fixed branding: navy #08306B with white text
# Column formatting
gt = (
    gt
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Big Color - price (msrp) gets colored as the primary neutral magnitude (Blues)
# Domain for msrp
msrp_cols = ["msrp"]
lo = float(np.nanmin(df[msrp_cols].to_numpy()))
hi = float(np.nanmax(df[msrp_cols].to_numpy()))

gt = (
    gt
    .data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band (branding tier)
gt = (
    gt
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
)

# Step 5: Small Color polish
# (a) Cell borders - hairlines between rows
gt = (
    gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# Frame - boxed border on all four sides
gt = (
    gt
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
)

# (c) Row striping - apply by default
gt = (
    gt
    .tab_options(row_striping_background_color="#F6F6F6")
    .opt_row_striping()
)

# (d) Stub tint - pale blue
gt = (
    gt
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
)

# Compact layout - padding values
gt = (
    gt
    .cols_width(cases={"hp": "100px", "msrp": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 6: Titles & Annotations
gt = (
    gt
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance and value across luxury automotive brands",
    )
)

# Footer notes (two separate calls as per the rule)
gt = (
    gt
    .tab_source_note(
        source_note="Price represents the manufacturer suggested retail price (MSRP). Horsepower is rated at engine peak RPM."
    )
    .tab_source_note(
        source_note="Source: GT Cars dataset."
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
