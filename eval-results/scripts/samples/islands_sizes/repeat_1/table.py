import numpy as np
import pandas as pd
from great_tables import GT
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize, hairlines

df = pd.read_csv("islands.csv")

cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns=cols, decimals=0, use_seps=True)
    .sub_missing(columns=cols, missing_text="—")
)

gt = heatmap(gt, "size", kind="sequential", hue="neutral", domain=[lo, hi])
gt = band(gt)
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

gt = (
    gt.tab_header(
        title="World Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
    .tab_source_note(source_note="Islands are ranked by size, with a color gradient showing relative magnitude.")
    .tab_source_note(source_note="Source: islands.csv")
)

gt = gt.cols_width(cases={"name": "150px", "size": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

finalize(gt, "table.png")
