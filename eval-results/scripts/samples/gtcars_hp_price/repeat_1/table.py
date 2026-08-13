import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

df = df[["mfr", "model", "hp", "msrp"]].copy()
df = df.dropna(subset=["hp", "msrp"])
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].reset_index(drop=True)

cols_hp = ["hp"]
cols_price = ["msrp"]

gt = (
    GT(df, rowname_col="car")
    .fmt_number(columns=cols_hp, decimals=0)
    .fmt_currency(columns=cols_price, currency="USD", decimals=0)
)

gt = heatmap(gt, columns=cols_price, kind="sequential", hue="neutral")

gt = (
    gt
    .cols_label(
        hp="Horsepower",
        msrp="Price (USD)",
    )
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance vehicles with their respective specifications",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .cols_width(cases={"hp": "100px", "msrp": "120px"})
)

gt = frame(gt)
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)

finalize(gt)
