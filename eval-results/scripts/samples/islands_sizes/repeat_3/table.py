import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import band, finalize, frame, heatmap, stripe, stub_tint

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .cols_label(size="Size (1000s km²)")
    .fmt_number(columns="size", decimals=1, use_seps=True)
    .sub_missing(columns="size", missing_text="—")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .cols_width(cases={"size": "140px"})
    .tab_header(
        title="World's Largest Islands",
        subtitle="Land area comparison across 49 major islands",
    )
)

gt = heatmap(gt, columns="size", kind="sequential", hue="Blues")
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

gt = (
    gt.tab_source_note(source_note="Island sizes ranked by land area in thousands of square kilometers.")
    .tab_source_note(source_note="Source: islands.csv")
)

finalize(gt)
