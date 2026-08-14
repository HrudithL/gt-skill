import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import band, hairlines, stripe, stub_tint, frame, finalize

df = pd.read_csv("islands.csv")

# Data cleaning: ensure size is numeric
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Sort by size for readability
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Compute domain for data_color
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Land area in thousands of square kilometers"
    )
    .cols_label(size="Size (1000s km²)")
    .fmt_number(columns="size", decimals=1)
    .data_color(
        columns="size",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Step 5(g): Compact layout
gt = gt.cols_width(cases={"name": "180px", "size": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 5(a): Column label styling
gt = gt.tab_style(style=style.text(color="white"), locations=loc.column_labels())

# Step 6: Titles & annotations
gt = gt.tab_source_note(source_note="Sizes represent the land area of major world islands in thousands of square kilometers.")
gt = gt.tab_source_note(source_note="Source: islands.csv")

# Step 4 & 5: Frame
gt = frame(gt)

# Step 7: Render
gt = finalize(gt, path="table.png")
