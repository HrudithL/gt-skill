import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="World Islands by Size",
        subtitle=md("Land area in thousands of square kilometers"),
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

gt = gt.cols_label(size="Size (1000 km²)")
gt = gt.cols_width(cases={"name": "180px", "size": "140px"})
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
gt = stub_tint(gt, hue="navy")

gt = gt.sub_missing(columns=["size"], missing_text="—")
gt = (
    gt.tab_source_note(source_note="Islands ranked by land area, largest first.")
    .tab_source_note(source_note="Source: geographic reference data.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
