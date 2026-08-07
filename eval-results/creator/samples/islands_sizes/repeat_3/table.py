import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

df = pd.read_csv("islands.csv")

tbl = (
    GT(df)
    .tab_header(
        title="Islands and Their Sizes",
        subtitle=md("Land area in thousands of square kilometers"),
    )
    .fmt_integer(columns="size")
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: islands.csv dataset")
)

tbl = humanize_labels(tbl, df, overrides={"size": "Size (thousand km²)"})
tbl = add_heatmap(tbl, df, "size")
tbl = apply_house_style(tbl)

tbl.gtsave("table.png", zoom=2, expand=10)
