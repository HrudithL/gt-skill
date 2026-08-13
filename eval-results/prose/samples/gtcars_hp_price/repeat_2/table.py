import numpy as np
import pandas as pd
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select and organize columns: manufacturer + model for stub, hp and msrp as measures
df = df[["mfr", "model", "hp", "msrp"]].copy()
df["car_name"] = df["mfr"] + " " + df["model"]
df = df[["car_name", "hp", "msrp"]].rename(columns={"car_name": "Car"})

# Step 2 & 3: Calculate domain for msrp heatmap (Blues palette, ordered magnitude)
cols = ["msrp"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5 & 6: Build the table
gt = (
    GT(df, rowname_col="Car")
    # Step 5(e): Format columns by semantic type
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0, use_seps=True)
    # Step 5(a): Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
    )
    # Step 5(c): Row striping (apply by default)
    .opt_row_striping()
    # Step 5(d): Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 3: Big Color - msrp heatmap (Blues, ordered magnitude, ≥5 rows)
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - fixed navy with white text (auto-contrasted)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    # Global constants: Frame border on all four sides
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
    .cols_width(cases={"hp": "100px", "msrp": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A collection of luxury and performance vehicles",
    )
    # Two separate footer notes (analytical caption + source)
    .tab_source_note(source_note="Price is colored to show relative market value across vehicles; horsepower is shown for reference.")
    .tab_source_note(source_note="Source: GT Cars dataset")
)

# Render with margin
gt.gtsave("table.png", expand=15)
