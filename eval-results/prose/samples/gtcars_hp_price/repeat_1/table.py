import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

# Step 1: Data validation — already clean (hp and msrp are floats)
# Step 2: Organize columns — build stub label from mfr + model (composite for readability)
df["car"] = df["mfr"] + " " + df["model"]
display_df = df[["car", "hp", "msrp"]].copy()
display_df.columns = ["Car", "Horsepower", "Price"]

# Compute domain for msrp (price) gradient
cols_color = ["Price"]
lo = float(np.nanmin(display_df[cols_color].to_numpy()))
hi = float(np.nanmax(display_df[cols_color].to_numpy()))

# Step 3: Big Color — msrp (price) is hero, hp stays plain (redundant dimensions)
# Step 4: Heading band — fixed navy branding tier
# Step 5: Small Color polish

gt = (
    GT(display_df, rowname_col="Car")
    # Step 3: Color gradient on Price (msrp) — Blues for neutral magnitude
    .data_color(
        columns=["Price"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — fixed navy, white text
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.column_labels(),
    )
    # Step 5a: Cell hairlines (body rows) — light grey
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5: Column label bottom rule
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5c: Row striping (default, always — body not 100% colored)
    .opt_row_striping()
    # Step 5d: Stub tint — fixed pale blue
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5e: Formatting per column
    .fmt_number(columns=["Horsepower"], decimals=0, use_seps=True)
    .fmt_currency(columns=["Price"], decimals=0)
    .sub_missing(columns=["Horsepower", "Price"], missing_text="—")
    # Step 5: Frame — light border all sides
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
    # Step 5: Compact layout — column widths + padding
    .cols_width(cases={"Car": "200px", "Horsepower": "110px", "Price": "110px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & Annotations
    .tab_header(
        title="GT Sports Cars: Horsepower and Price",
        subtitle="Performance metrics for premium automotive models",
    )
    # Step 6f: Two footer calls (analytical caption + source)
    .tab_source_note("Price encoded by magnitude using sequential Blues palette; horsepower shown as reference metric.")
    .tab_source_note("Source: gtcars.csv (sports car market data, 2014–2017).")
)

gt.gtsave("table.png", expand=15, zoom=2.0)
