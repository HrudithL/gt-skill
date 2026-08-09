import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap

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
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_header(
        title="Islands of the World",
        subtitle="Land area in thousands of square miles"
    )
    .tab_source_note("Source: provided dataset")
)

gt = frame(gt)
finalize(gt, "table.png")
