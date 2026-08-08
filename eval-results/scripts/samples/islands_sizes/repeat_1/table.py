import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
        column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
        column_labels_border_bottom_width="2px",
    )
)

gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, shade="light", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = (
    gt
    .tab_header(
        title="World's Largest Islands",
        subtitle="Island sizes in thousands of square kilometers"
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = frame(gt)
finalize(gt, "table.png")
