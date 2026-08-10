import pandas as pd
from great_tables import GT
from house_table import PALETTE, frame, hairlines, finalize, band, heatmap, humanize_labels

df = pd.read_csv("gtcars.csv")

# Create composite car identifier (mfr + model)
df["car"] = df["mfr"] + " " + df["model"]

# Select and sort by horsepower descending
display_df = df[["car", "hp", "msrp"]].sort_values("hp", ascending=False).reset_index(drop=True)

gt = (
    GT(display_df, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="High-performance vehicles ranked by engine output"
    )
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={"hp": "Horsepower", "msrp": "Price (MSRP)"}
)

# Big Color: horsepower as the sequential hero (Blues/neutral — a plain magnitude)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

# Heading band: navy to match the Blues heatmap
gt = band(gt, hue="navy")

# No striping gate check: 48 rows > 10, and only 1 column is colored (hp),
# so body is not "essentially fully covered" — stripe applies.
from house_table import stripe
gt = stripe(gt)

# Stub tint harmonizes to navy
from house_table import stub_tint
gt = stub_tint(gt, hue="navy")

gt = gt.tab_source_note(source_note="Source: provided dataset.")
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
