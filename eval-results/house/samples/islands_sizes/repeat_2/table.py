import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, humanize_labels

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="World Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .tab_source_note(
        source_note="Ranked by land area in thousands of square kilometers."
    )
    .tab_source_note(
        source_note="Source: provided dataset."
    )
)

gt = humanize_labels(gt, df, overrides={"size": "Size (1000 km²)"})

gt = gt.cols_width(
    cases={
        "name": "180px",
        "size": "140px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
