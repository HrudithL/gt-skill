import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")
df = df[["mfr", "model", "hp", "msrp"]].copy()
df = df.dropna(subset=["hp", "msrp"])
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Step 2: Organize columns with stub
gt = GT(df, rowname_col="Manufacturer")

# Step 3: Big Color - Price qualifies (ordered magnitude, ≥5 rows, neutral magnitude → Blues)
gt = heatmap(gt, "Price", kind="sequential", hue="neutral")

# Step 3b: Format Horsepower (hero measure that's not colored, needs bold)
gt = gt.fmt_number(columns="Horsepower", decimals=0, use_seps=True)

# Step 4: Heading band - light band for Blues Big Color
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color polish
gt = gt.fmt_currency(columns="Price", decimals=0, currency="USD")
gt = gt.tab_options(
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Apply bold to the uncolored Horsepower column
gt = gt.tab_style(
    style=style.text(weight="bold"),
    locations=loc.body(columns="Horsepower")
)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="GT Cars: Horsepower and Price",
    subtitle="Premium performance vehicles by manufacturer"
)
gt = gt.tab_source_note(source_note="Price colored by magnitude to show relative cost across the lineup.")
gt = gt.tab_source_note(source_note="Source: gtcars.csv")

# Global constants: Frame
gt = frame(gt)

# Step 7: Render
finalize(gt, "table.png")
