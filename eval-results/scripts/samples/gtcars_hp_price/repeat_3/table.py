import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, band, frame, finalize, stripe, stub_tint, hairlines

df = pd.read_csv("gtcars.csv")

cols_to_show = ["mfr", "model", "hp", "msrp"]
df = df[cols_to_show].copy()

df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]].reset_index(drop=True)

cols_measure = ["msrp"]
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

gt = (
    GT(df, rowname_col="car")
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0, currency="USD")
    .data_color(
        columns="msrp",
        palette="Greens",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .cols_width(cases={"car": "240px", "hp": "100px", "msrp": "140px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_header(
        title="GT Cars: Horsepower and MSRP",
        subtitle="High-performance vehicles by manufacturer"
    )
    .tab_source_note(source_note="Price is the primary measure (colored); horsepower provides context as a secondary metric.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt = band(gt)
gt = stripe(gt)
gt = hairlines(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = finalize(gt)
