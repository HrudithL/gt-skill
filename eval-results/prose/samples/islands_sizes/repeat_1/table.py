import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("islands.csv")

cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

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
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
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
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_header(
        title="Islands of the World",
        subtitle="Size in thousands of square kilometers"
    )
    .tab_source_note(source_note="Island sizes range from 11,506 (Africa) to 12 thousand square kilometers (Vancouver).")
    .tab_source_note(source_note="Source: Islands dataset.")
)

gt.gtsave("table.png", expand=15)
