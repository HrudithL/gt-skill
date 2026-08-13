import numpy as np
import pandas as pd
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Read and clean the data
df = pd.read_csv("islands.csv")
df["size"] = pd.to_numeric(df["size"], errors="coerce")

# Step 2: Organize columns — name is stub, size is the measure
# Step 3: Big Color — size qualifies (≥5 rows, ordered numeric magnitude, neutral semantics)
cols_to_color = ["size"]
lo = float(np.nanmin(df[cols_to_color].to_numpy()))
hi = float(np.nanmax(df[cols_to_color].to_numpy()))

gt = (
    GT(df, rowname_col="name")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .sub_missing(columns="size", missing_text="—")
)

# Step 3: Apply heatmap (sequential, neutral magnitude → Blues)
gt = heatmap(gt, cols_to_color, kind="sequential", hue="neutral", domain=[lo, hi])

# Step 4: Heading band (fixed navy, bold labels, white text)
gt = band(gt)

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Tab options for compact layout
gt = (
    gt.tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .cols_width(cases={"name": "200px", "size": "120px"})
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 6: Titles & Annotations
gt = (
    gt.tab_header(
        title="World's Largest Islands",
        subtitle="Island sizes in thousands of square miles"
    )
    .tab_source_note(source_note="Size represents the area of each island in thousands of square miles.")
    .tab_source_note(source_note="Source: islands.csv")
)

# Step 7: Render
finalize(gt, "table.png")
