import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import heatmap, band, frame, finalize, hairlines, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

# Step 1: Clean data
df = df[["mfr", "model", "hp", "msrp"]].dropna(subset=["hp", "msrp"])
df["car"] = df["mfr"] + " " + df["model"]

# Step 2: Organize columns
df_display = df[["car", "hp", "msrp"]].reset_index(drop=True)

# Step 3: Big Color — price is the hero measure (neutral magnitude)
cols_color = ["msrp"]
lo = float(np.nanmin(df_display[cols_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_color].to_numpy()))

gt = (
    GT(df_display, rowname_col="car")
    .fmt_number(columns=["hp"], decimals=0)
    .fmt_currency(columns=["msrp"], decimals=0)
    .data_color(
        columns=cols_color,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band
    .tab_header(
        title="GT Cars Specifications",
        subtitle="Horsepower and Price"
    )
    # Step 2b: Column sizing
    .cols_width(cases={
        "hp": "80px",
        "msrp": "120px",
    })
    # Step 5: Small Color polish
    .tab_options(
        heading_padding="12px",
        column_labels_padding="12px",
        column_labels_padding_horizontal="12px",
        data_row_padding="8px",
        data_row_padding_horizontal="12px",
        source_notes_padding="12px",
    )
)

gt = stripe(gt)
gt = stub_tint(gt)
gt = band(gt)
gt = frame(gt)
gt = hairlines(gt)
finalize(gt)
