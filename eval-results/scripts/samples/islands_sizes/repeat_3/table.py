import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("islands.csv")

cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns=cols, decimals=0)
    .data_color(
        columns=cols,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square kilometers"
    )
    .opt_row_striping()
)

gt = band(gt, shade="light", hue="navy")
gt = frame(gt, color="#CCCCCC", width="2px")
gt = finalize(gt)

gt.gtsave("table.png")
