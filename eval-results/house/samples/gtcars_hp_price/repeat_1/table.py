import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("gtcars.csv")

# Select and reorder columns
df = df[["mfr", "model", "hp", "msrp"]].copy()
df = df.rename(columns={"mfr": "manufacturer"})
df = df.sort_values("hp", ascending=False)

gt = (
    GT(df, rowname_col="model")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("Performance metrics for high-performance vehicles"),
    )
    .tab_stubhead(label="Model")
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(gt, df, overrides={"hp": "Horsepower", "msrp": "MSRP"})

# Color the horsepower column (sequential heatmap)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

# Band and striping
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Render
finalize(gt, path="table.png")
