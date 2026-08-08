import pandas as pd
from great_tables import GT, loc, style
from house_table import PALETTE, frame, finalize, heatmap, humanize_labels

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers",
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

gt = humanize_labels(gt, df)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)
gt = gt.tab_source_note(source_note="Source: provided dataset.")
gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
