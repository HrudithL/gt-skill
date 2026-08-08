import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and rename for display
df = df[["mfr", "model", "hp", "msrp"]].copy()
df["car"] = df["mfr"] + " " + df["model"]
df = df[["car", "hp", "msrp"]]
df = df.rename(columns={"car": "Car"})

# Step 2: Organize columns - Car is the stub, hp and msrp are measures
gt = (
    GT(df, rowname_col="Car")
    .cols_label(hp="Horsepower", msrp="Price (MSRP)")
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Step 3: Color the two measures - both are neutral magnitudes
# Primary: hp (mentioned first in prompt) → Blues (sequential)
# Secondary: msrp → Greens (sequential, per tie-breaker rule for two neutral measures)
gt = heatmap(gt, columns="hp", kind="sequential", hue="neutral")
gt = heatmap(gt, columns="msrp", kind="sequential", hue="positive")

# Step 4: Heading band - light band with Blues tint (navy hue)
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color polish
# (a) Cell borders - hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# (c) Row striping - 30+ rows
gt = stripe(gt)

# (d) Stub tint - harmonized to Blues tint (navy)
gt = stub_tint(gt, hue="navy")

# (f) Titles - Step 6
gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle="Performance and value across premium sports cars",
)

# Step 7: Frame and finalize
gt = frame(gt)
gt = finalize(gt)
