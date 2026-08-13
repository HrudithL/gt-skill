import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import band, stripe, stub_tint, heatmap, frame, finalize

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
    .cols_label(name="Island", size="Size (1000 km²)")
    .cols_width(cases={"name": "180px", "size": "120px"})
    .tab_header(
        title="Islands of the World",
        subtitle="Land areas by size"
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
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
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_style(
        style=style.borders(sides="top", color="#08306B", weight="3px"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.column_labels(),
    )
    .tab_source_note(source_note="Size represents approximate land area in thousands of square kilometers.")
    .tab_source_note(source_note="Source: Geographic reference data.")
)

gt.gtsave("table.png", expand=15, zoom=2.0)
