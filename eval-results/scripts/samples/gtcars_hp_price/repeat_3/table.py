import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, band, stripe, stub_tint, frame, finalize, heatmap, hairlines

df = pd.read_csv("gtcars.csv")

df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].copy()
df = df.dropna(subset=["hp", "msrp"])
df = df.sort_values("msrp", ascending=False).reset_index(drop=True)

gt = (
    GT(df, rowname_col="car")
    .fmt_number(columns=["hp"], decimals=0, use_seps=True)
    .fmt_currency(columns=["msrp"], decimals=0)
    .sub_missing(missing_text="—")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Sorted by MSRP"
    )
    .tab_spanner(label="Specifications", columns=["hp", "msrp"])
)

gt = heatmap(gt, columns=["msrp"], kind="sequential", hue="neutral")

gt = band(gt)

gt = hairlines(gt)

gt = (
    gt.tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="hp"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="hp"),
    )
)

gt = stripe(gt)
gt = stub_tint(gt)

gt = (
    gt.cols_width(cases={"car": "200px", "hp": "120px", "msrp": "140px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = (
    gt.tab_source_note(source_note="Price is the primary measure for comparing overall vehicle value; horsepower provides context on engine capability.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt = frame(gt)
finalize(gt)
