import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Load and clean data
df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

# Step 1: Data is clean (name and size columns, numeric values)
# Step 2: Island names are the stub, size is the measure
# Step 3: Size qualifies for Big Color (sequential, ≥5 rows, ordered magnitude)
# Compute domain for size
cols = ["size"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))

# Build table
gt = GT(df, rowname_col="name")

# Step 3: Apply gradient fill to size column (Blues for neutral magnitude)
gt = heatmap(gt, "size", kind="sequential", hue="neutral", domain=[lo, hi])

# Step 5: Format the size column
gt = gt.fmt_number(columns="size", decimals=0, use_seps=True)

# Step 5: Apply striping (≥10 rows, body not fully filled by Big Color on stub)
gt = stripe(gt)

# Step 5: Stub tint with grey (no Big Color dominance requiring washed tint)
gt = stub_tint(gt, hue="grey")

# Step 4: Light band with washed blue tint (Big Color present)
gt = band(gt, shade="light", hue="navy")

# Add frame and render
gt = frame(gt)
gt = gt.tab_header(
    title="World's Largest Islands",
    subtitle="Islands ranked by land area (thousand sq km)"
)
finalize(gt, "table.png")
