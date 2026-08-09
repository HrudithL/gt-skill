import numpy as np
import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, frame, stripe, finalize

# Step 1: UNDERSTAND THE DATA
df = pd.read_csv("islands.csv")
# Data is clean: name (string), size (numeric in thousands of km²)
# 49 islands, no missing values, correctly typed

# Step 2: ORGANIZE COLUMNS
# name → stub (row identifiers), size → hero measure
gt = GT(df, rowname_col="name")

# Step 3: BIG COLOR — size is an ordered numeric magnitude (neutral quantity → Blues)
cols_measure = ["size"]
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Apply heatmap coloring (size is a neutral magnitude → Blues via "neutral" semantic)
gt = heatmap(gt, cols_measure, kind="sequential", hue="neutral", domain=[lo, hi])

# Step 4: HEADING BAND — with Big Color present, use light band
gt = band(gt, shade="light", hue="navy")

# Step 5: SMALL COLOR — apply the polish checklist
# (a) Cell borders — hairline between rows (default) + column-label bottom rule
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (c) Row striping — ≥10 rows and not fully filled by Big Color → stripe
gt = stripe(gt)

# (d) Stub tint — use light grey (grey budget not strained here)
gt = gt.tab_style(
    style=style.fill(color="#F0F0F0"),
    locations=loc.stub(),
)

# (e) Format the size column as a plain number with thousands separator
gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)

# Step 6: TITLES & ANNOTATIONS
gt = gt.tab_header(
    title="Island Sizes",
    subtitle="Land area in thousands of square kilometers"
)

# Footer: analytical caption (defines the data) + source note
gt = gt.tab_source_note(source_note="Data represents the largest islands worldwide, with areas measured in thousands of square kilometers.")
gt = gt.tab_source_note(source_note="Source: islands.csv")

# Step 7: FRAME & RENDER
gt = frame(gt)
finalize(gt)
