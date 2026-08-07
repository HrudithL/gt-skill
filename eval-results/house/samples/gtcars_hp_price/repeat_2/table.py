import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Read the GT cars data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and prepare data
df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["manufacturer", "model", "hp", "msrp"]

# Create the GT table
gt = (
    GT(df)
    .tab_header(
        title="GT Cars Performance",
        subtitle=md("Horsepower and price for high-performance vehicles"),
    )
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

# Apply house style helpers
gt = humanize_labels(gt, df)

# Apply heatmap to horsepower (sequential magnitude)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

# Apply heading band
gt = band(gt, hue="navy")

# Add source note and frame
gt = (
    gt.tab_source_note(source_note="Source: GT Cars dataset.")
)

gt = frame(gt)
finalize(gt, path="table.png")
