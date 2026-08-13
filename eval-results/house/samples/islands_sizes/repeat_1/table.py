import pandas as pd
from great_tables import GT, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers",
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .cols_label(size="Area (1000 km²)")
    .cols_width(cases={"name": "140px", "size": "110px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = (
    gt.tab_source_note(
        source_note="Areas represent the largest islands in the world, measured in thousands of square kilometers."
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
