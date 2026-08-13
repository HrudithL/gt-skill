import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import band, frame, finalize, heatmap, stripe, stub_tint

df = pd.read_csv("islands.csv")

cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .cols_label(size="Size (1000s km²)")
    .cols_width(cases={"size": "140px"})
    .fmt_number(columns="size", decimals=0, use_seps=False)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Island Sizes",
        subtitle="Area measurements for major islands worldwide",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
)

gt = stripe(gt)
gt = band(gt)
gt = frame(gt)
finalize(gt, "table.png")
