import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap
)

# Read the data
df = pd.read_csv("islands.csv")

# Create the GT table
gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="World's Largest Islands",
        subtitle="Land area in thousands of square kilometers"
    )
    .fmt_integer(columns="size", sep_mark=",")
    .tab_source_note(
        source_note="Ranked by total land area."
    )
    .tab_source_note(
        source_note="Source: provided dataset."
    )
)

# Apply the house-format styling
gt = frame(gt)
gt = hairlines(gt)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)

# Finalize and render
finalize(gt, path="table.png")
