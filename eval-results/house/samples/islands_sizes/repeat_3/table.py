import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

def build_islands_table():
    df = pd.read_csv("islands.csv")

    gt = GT(df, rowname_col="name")
    gt = gt.tab_header(
        title="World's Largest Islands",
        subtitle=md("Land area by island, in thousands of square kilometers")
    )
    gt = gt.tab_stubhead(label="Island")

    gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)
    gt = humanize_labels(
        gt,
        df,
        overrides={"size": "Area (1000 km²)"}
    )

    gt = gt.cols_width(cases={"name": "150px", "size": "100px"})
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

    gt = gt.tab_source_note(
        source_note="Island sizes sorted by area in descending order."
    )
    gt = gt.tab_source_note(source_note="Source: provided dataset.")

    gt = hairlines(gt)
    gt = frame(gt)
    finalize(gt)

if __name__ == "__main__":
    build_islands_table()
