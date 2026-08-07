import numpy as np
import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df["size"] = pd.to_numeric(df["size"], errors="coerce")
df = df.dropna()

# Step 2: Organize columns
# Island name is the stub (identifier), size is the measure
cols = ["size"]

# Step 3: Big Color — sequential Blues for ordered magnitude (neutral)
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Step 4 & 5: Build table with band, color, and polish
gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns=cols, decimals=0, use_seps=True)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — light washed tint (Blues table)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5c: Row striping (≥10 rows)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5d: Stub tint harmonized to washed blue
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5e: Format missing values
    .sub_missing(columns=cols, missing_text="—")
    # Global frame
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
    # Titles
    .tab_header(
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
)

gt.gtsave("table.png", expand=15)
