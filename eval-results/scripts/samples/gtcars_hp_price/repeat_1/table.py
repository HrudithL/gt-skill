import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

# Step 1: Ensure numeric columns are clean
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Step 2: Create stub identifier (mfr + model) and organize columns
df["car"] = df["mfr"] + " " + df["model"]
display_df = df[["car", "hp", "msrp"]].copy()

# Step 3 & 4: Build table with Big Color (two measures: msrp and hp)
# msrp is primary (neutral magnitude → Blues)
# hp is secondary (neutral magnitude → Greens as fallback)
gt = (
    GT(display_df, rowname_col="car")
    .fmt_currency(columns="msrp", decimals=0, use_seps=True)
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Step 3: Apply Big Color (two measures)
# Primary: msrp (price) → Blues
lo_msrp = float(np.nanmin(display_df[["msrp"]].to_numpy()))
hi_msrp = float(np.nanmax(display_df[["msrp"]].to_numpy()))
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral", domain=[lo_msrp, hi_msrp])

# Secondary: hp → Greens (fallback from Blues → Greens → Oranges rule)
lo_hp = float(np.nanmin(display_df[["hp"]].to_numpy()))
hi_hp = float(np.nanmax(display_df[["hp"]].to_numpy()))
gt = heatmap(gt, "hp", kind="sequential", hue="positive", domain=[lo_hp, hi_hp])

# Step 4: Light heading band (Big Color present, matched to primary Blue hue)
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color polish
gt = frame(gt)
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Rename columns for display
gt = (
    gt.cols_label(hp="Horsepower", msrp="Price (MSRP)")
    .tab_stubhead(label="Car Model")
)

# Step 6: Titles and annotations
gt = (
    gt.tab_header(
        title="GT Cars: Horsepower vs. Price",
        subtitle="High-performance vehicle specifications"
    )
    .tab_source_note(source_note="Source: GT Cars dataset")
)

# Step 7: Render
finalize(gt, "table.png")
