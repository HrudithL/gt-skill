import pandas as pd
from great_tables import GT
from house_table import PALETTE, frame, finalize, band, heatmap

df = pd.read_csv("gtcars.csv")

# Select and display the relevant columns: manufacturer, model, hp, and msrp
display_df = df[["mfr", "model", "hp", "msrp"]].copy()

gt = (
    GT(display_df)
    .tab_header(
        title="GT Cars Database",
        subtitle="Horsepower and Price for High-Performance Vehicles",
    )
    .fmt_number(columns="hp", decimals=0, use_seps=False)
    .fmt_currency(columns="msrp", decimals=0)
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        hp="Horsepower",
        msrp="Price",
    )
    .tab_source_note(source_note="Source: GT Cars dataset")
)

# Apply heatmap to msrp (price as primary measure in Blues)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply band styling
gt = band(gt, hue="navy")

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt)
