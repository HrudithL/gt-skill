import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE,
    frame,
    hairlines,
    finalize,
    band,
    stripe,
    heatmap,
)

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle=md("Land area in thousands of square kilometers"),
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

# Column-label band with dark navy background
gt = band(gt, hue="navy")

# Heatmap for the size column — sequential Blues for a neutral magnitude
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Striping since not all columns are heatmap-covered
gt = stripe(gt)

# Source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Sizes represent land area in thousands of square kilometers."
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset."
)

# Polish: frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

finalize(gt)
