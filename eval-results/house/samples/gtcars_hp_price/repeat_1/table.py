import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, stripe, stub_tint, humanize_labels

df = pd.read_csv("gtcars.csv")

# Select and organize columns: model (stub), horsepower, and price
gt_data = df[["model", "hp", "msrp"]].copy()
gt_data.columns = ["model", "horsepower", "price"]

gt = (
    GT(gt_data, rowname_col="model")
    .tab_header(
        title="GT Cars Performance & Price",
        subtitle=md("Horsepower and MSRP for high-performance vehicles"),
    )
    .tab_stubhead(label="Model")
    .fmt_number(columns="horsepower", decimals=0, use_seps=True)
    .fmt_currency(columns="price", decimals=0)
    .sub_missing(columns=["horsepower", "price"], missing_text="—")
)

gt = humanize_labels(gt, gt_data, overrides={})

# Single sequential heatmap on price (the key measure)
gt = (
    gt.data_color(
        columns="price",
        palette="Blues",
        domain=[gt_data["price"].min(), gt_data["price"].max()],
        na_color=PALETTE["neutral"]["na_cell"],
        truncate=False,
        autocolor_text=True,
    )
)

# Heading band with neutral styling
gt = gt.tab_options(
    column_labels_background_color="#F0F0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Striping and stub tint for visual clarity
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Add source note and frame
gt = (
    gt.tab_source_note(source_note="Source: provided dataset.")
    .pipe(frame)
)

finalize(gt, path="table.png", zoom=2.0, expand=15)
