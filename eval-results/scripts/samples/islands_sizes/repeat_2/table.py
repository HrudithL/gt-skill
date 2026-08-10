import numpy as np
import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("islands.csv")

# Step 3: Compute domain for column_gradient_fill
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Build table
gt = (
    GT(df, rowname_col="name")
    # Step 5(e): Format the numeric column
    .fmt_number(columns="size", decimals=0, use_seps=True)
    # Step 3: Big Color — ordered magnitude gradient
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 5(a): Cell borders — hairline between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Step 4: Heading band — light with column-label bottom rule
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5(d): Stub tint — washed-DA Navy tint (grey-budget harmonization)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5(c): Row striping (≥10 rows and body not fully filled)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Global constant: Frame — boxed light border
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
    # Step 6: Titles and annotations
    .tab_header(
        title="Island Sizes",
        subtitle="Land area by island (in square kilometers)"
    )
    .tab_source_note(source_note="Islands ranked by size, from largest (Africa) to smallest (Vancouver).")
    .tab_source_note(source_note="Source: islands.csv")
)

gt.gtsave("table.png", expand=15)
