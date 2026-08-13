import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

df = pd.read_csv("gtcars.csv")

# Build row identifier as mfr + model
df["car"] = df["mfr"] + " " + df["model"]

# Sort by price descending for visual interest
df = df.sort_values("msrp", ascending=False).reset_index(drop=True)

# Select and rename columns
df_table = df[["car", "hp", "msrp"]].copy()
df_table.columns = ["car", "hp", "msrp"]

gt = (
    GT(df_table, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("High-performance vehicles sorted by price"),
    )
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    df_table,
    overrides={"hp": "Horsepower", "msrp": "Price"},
)

gt = gt.cols_width(
    cases={
        "car": "200px",
        "hp": "120px",
        "msrp": "140px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

gt = band(gt, hue="navy")

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = (
    gt.tab_source_note(
        source_note="Data shows horsepower and manufacturer suggested retail price (MSRP) for each vehicle."
    )
    .tab_source_note(source_note="Source: provided dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
