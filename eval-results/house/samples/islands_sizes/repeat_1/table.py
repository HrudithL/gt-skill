import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Islands by Size",
        subtitle=md("Land area in thousands of square kilometers")
    )
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = humanize_labels(gt, df)

gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = gt.tab_source_note(
    source_note="Size represents land area in thousands of square kilometers."
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset."
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
