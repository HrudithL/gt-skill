import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create stub label (manufacturer + model)
df["car"] = df["mfr"] + " " + df["model"]

# Select and prepare columns
df_display = df[["car", "hp", "msrp"]].copy()
df_display = df_display.rename(columns={"car": "Car", "hp": "Horsepower", "msrp": "MSRP"})

# Step 2: Create GT table with stub
gt = GT(df_display, rowname_col="Car")

# Step 3: Big Color — only MSRP gets heatmap (Blues for neutral magnitude)
lo = float(np.nanmin(df_display[["MSRP"]].to_numpy()))
hi = float(np.nanmax(df_display[["MSRP"]].to_numpy()))
gt = gt.data_color(
    columns="MSRP",
    palette="Blues",
    domain=[lo, hi],
    truncate=False,
    na_color="#808080",
)

# Step 4: Heading band — fixed navy, bold labels (white text auto-applies)
gt = gt.tab_options(
    column_labels_background_color="#08306B",
    column_labels_font_weight="bold",
)

# Step 5: Small Color Polish

# (a) Cell borders — hairlines between rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Frame — boxed border on all four sides
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

# (c) Row striping
gt = gt.opt_row_striping()
gt = gt.tab_options(row_striping_background_color="#F6F6F6")

# (d) Stub tint
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# (e) Formatting per column
gt = gt.fmt_number(columns="Horsepower", decimals=0, use_seps=True)
gt = gt.fmt_currency(columns="MSRP", decimals=0, use_seps=True)
gt = gt.sub_missing(columns=["Horsepower", "MSRP"], missing_text="—")

# Compact layout padding
gt = gt.cols_width(cases={"Horsepower": "120px", "MSRP": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & Annotations
gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle="Performance and value across high-performance vehicles",
)

# Two footer notes: analytical caption + source
gt = gt.tab_source_note(
    source_note="Price (MSRP) is color-coded to show relative values across the dataset; horsepower is shown as plain text for reference."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv"
)

# Render
gt.gtsave("table.png", expand=15)
