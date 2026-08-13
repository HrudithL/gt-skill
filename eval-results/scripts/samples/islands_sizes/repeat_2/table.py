import numpy as np
import pandas as pd
from great_tables import GT, loc, style
from gt_consistency import PALETTE, heatmap, band, stripe, stub_tint, frame, hairlines, finalize

df = pd.read_csv("islands.csv")

cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns=cols, decimals=0, use_seps=True)
)

gt = heatmap(gt, columns=cols, kind="sequential", hue="neutral", domain=[lo, hi])
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = hairlines(gt)

gt = (
    gt
    .tab_header(
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers",
    )
    .tab_source_note("Data shows the area of islands across the world.")
)

finalize(gt, "table.png")
