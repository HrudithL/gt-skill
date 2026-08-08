import pandas as pd
from great_tables import GT
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("islands.csv")
df = df.dropna()

# Step 2: Organize columns
# Island name is the stub, size is the measure
gt = GT(df, rowname_col="name")

# Step 3: Big Color — size column qualifies as ordered magnitude (≥5 rows, neutral semantic)
# Use sequential Blues palette
gt = gt.fmt_number(columns="size", decimals=0)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Step 4: Heading band — with Big Color, use light band with forest hue (matching data semantics)
gt = band(gt, shade="light", hue="forest")

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")
gt = frame(gt)

# Step 6: Titles and annotations
gt = gt.tab_header(
    title="World's Largest Islands",
    subtitle="Area in thousands of square kilometers"
)
gt = gt.tab_source_note(
    "Source: Geographic data"
)

finalize(gt, "table.png")
