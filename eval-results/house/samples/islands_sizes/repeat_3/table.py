import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, heatmap, humanize_labels

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle=md("Area in thousands of square kilometers"),
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

gt = humanize_labels(gt, df)

gt = gt.cols_width(cases={"name": "180px", "size": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, hue="navy")
gt = stripe(gt)

gt = (
    gt.tab_source_note(
        source_note="Area measured in thousands of square kilometers."
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
