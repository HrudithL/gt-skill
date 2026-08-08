import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, heatmap, humanize_labels

# Read the GT cars data
df = pd.read_csv("gtcars.csv")

# Select only relevant columns and create a display-friendly version
display_df = df[["mfr", "model", "hp", "msrp"]].copy()
display_df.columns = ["manufacturer", "model", "horsepower", "price"]

# Create the GT table
gt = GT(display_df).tab_header(
    title="GT Cars — Horsepower & Price",
    subtitle=md("Performance cars ranked by power and market value"),
).fmt_number(
    columns="horsepower",
    decimals=0,
).fmt_currency(
    columns="price",
    decimals=0,
)

# Humanize column labels
gt = humanize_labels(gt, display_df)

# Apply heatmap to price (sequential neutral -> Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Apply frame and finalize
gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
