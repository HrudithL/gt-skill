import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create stub: combine manufacturer + model
df["car"] = df["mfr"] + " " + df["model"]

# Select only the columns we need
df = df[["car", "hp", "msrp"]]

# Step 2: Organize columns (stub is "car", show hp then msrp)
# msrp (price) is the hero measure for color, hp is secondary/supporting

# Step 3: Big Color — only msrp qualifies as colored
# hp and msrp are near-redundant (both proxy "how impressive"), so msrp is hero, hp stays plain
cols_to_color = ["msrp"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))

# Step 4 & 5 & 6: Build the table with all formatting
gt = (
    GT(df, rowname_col="car")
    # Step 5(e): Format columns
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Step 3: Big Color — gradient fill on msrp only (price)
    .data_color(
        columns=cols_to_color,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — fixed navy with white text
    .tab_options(
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5(a): Cell borders — hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5(c): Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5(d): Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Compact layout — column widths and padding
    .cols_width(cases={"hp": "100px", "msrp": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame — boxed border on all sides
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
    # Step 6: Title, subtitle, and footer
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A selection of high-performance vehicles with engine and market data"
    )
    .tab_source_note(
        source_note="Price (MSRP) is displayed with a blue gradient to show relative market values across the vehicle selection."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
