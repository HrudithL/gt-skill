import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, humanize_labels, heatmap

# Load data
df = pd.read_csv("gtcars.csv")

# Create car identifier as stub column
df["car"] = df["mfr"] + " " + df["model"]

# Select and sort columns
gt_cars = df[["car", "hp", "msrp"]].copy()
gt_cars.columns = ["car", "horsepower", "price"]

# Create table
gt = (
    GT(gt_cars, rowname_col="car")
    .tab_header(
        title="GT Sports Cars",
        subtitle="Horsepower and price for performance vehicles"
    )
    .fmt_number(columns="horsepower", decimals=0)
    .fmt_currency(columns="price", decimals=0)
)

# Apply labels with overrides
gt = humanize_labels(
    gt,
    gt_cars,
    overrides={"horsepower": "Horsepower", "price": "Price (USD)"}
)

# Single colored measure: price (sequential, neutral palette for currency)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Apply styling
gt = band(gt, hue="navy")
gt = hairlines(gt)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: gtcars dataset")

finalize(gt, path="table.png")
