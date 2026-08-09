import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap

# Read the data
cars = pd.read_csv("gtcars.csv")

# Select relevant columns: manufacturer, model, horsepower, and price (msrp)
cars_subset = cars[["mfr", "model", "hp", "msrp"]].copy()
cars_subset.columns = ["mfr", "model", "horsepower", "price"]

gt = (
    GT(cars_subset)
    .tab_header(
        title="GT Cars Horsepower and Price",
        subtitle=md("High-performance vehicles with engine power and MSRP"),
    )
    .fmt_number(columns="horsepower", decimals=0, use_seps=False)
    .fmt_currency(columns="price", decimals=0)
)

gt = humanize_labels(
    gt,
    cars_subset,
    overrides={"mfr": "Manufacturer", "model": "Model", "horsepower": "Horsepower (hp)", "price": "MSRP"},
)

# Apply heatmap to price (the single colored measure)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Column-label band (light tint, navy)
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

gt = gt.tab_source_note(source_note="Source: gtcars.csv dataset.")

# Frame and finalize
gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
