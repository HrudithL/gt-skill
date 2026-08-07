import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, heatmap, humanize_labels

# Load the data
df = pd.read_csv("gtcars.csv")

# Select and prepare columns: manufacturer, model, horsepower, and price (msrp)
cars = df[["mfr", "model", "hp", "msrp"]].copy()
cars.columns = ["manufacturer", "model", "horsepower", "price"]

# Create the table
gt = (
    GT(cars)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("High-performance vehicles with engine power and MSRP")
    )
    .fmt_number(columns="horsepower", decimals=0)
    .fmt_currency(columns="price", currency="USD", decimals=0)
)

# Apply house-format helpers
gt = humanize_labels(
    gt,
    cars,
    overrides={
        "manufacturer": "Manufacturer",
        "model": "Model",
        "horsepower": "Horsepower (hp)",
        "price": "Price (MSRP)"
    }
)

# Single colored measure: price as a neutral sequential heatmap (Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Heading band with navy accent
gt = band(gt, hue="navy")

# Add source note and frame
gt = (
    gt.tab_source_note(source_note="Source: provided dataset.")
)
gt = frame(gt)
finalize(gt, path="table.png")
