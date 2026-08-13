import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize, PALETTE

df = pd.read_csv("gtcars.csv")

# Step 1: Prepare data
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].copy()
df.columns = ["car", "Horsepower", "Price"]

# Step 2: Organize columns
# car is stub, hp and msrp as measures

# Step 3: Big Color — price qualifies as ordered magnitude, hp is redundant
cols_price = ["Price"]
lo = float(np.nanmin(df[cols_price].to_numpy()))
hi = float(np.nanmax(df[cols_price].to_numpy()))

# Step 4 & 5: Build table with heading band, striping, stub tint, borders, frame
gt = (
    GT(df, rowname_col="car")
    .fmt_number(columns=["Horsepower"], decimals=0, use_seps=True)
    .fmt_currency(columns=["Price"], decimals=0)
    .data_color(
        columns=cols_price,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Heading band (Step 4)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Cell borders (Step 5a)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Stub tint (Step 5d)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Row striping (Step 5c)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Frame borders (global constant)
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
    # Compact layout (Step 5g)
    .cols_width(cases={"car": "200px", "Horsepower": "130px", "Price": "140px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles & annotations (Step 6)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="2014–2017 production models",
    )
    # Footer (Step 5f) — two separate calls
    .tab_source_note(
        source_note="Price is shown as the primary measure of car value. Horsepower is displayed for reference but not colored, as both metrics serve as proxies for the same underlying concept of car performance."
    )
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt.gtsave("table.png", expand=15, zoom=2.0)
