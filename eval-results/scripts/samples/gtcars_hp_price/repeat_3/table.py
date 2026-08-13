import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint, hairlines

df = pd.read_csv("gtcars.csv")

# Select relevant columns - use mfr as stub (row identifier)
display_df = df[["mfr", "model", "hp", "msrp"]].copy()

# Create the GT table with mfr as stub (row identifier)
gt = (
    GT(display_df, rowname_col="mfr")
    .cols_label(
        model="Model",
        hp="Horsepower (hp)",
        msrp="Price (USD)"
    )
    .cols_width(cases={"model": "200px", "hp": "120px", "msrp": "140px"})
    .fmt_integer(columns="hp")
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
    .tab_header(
        title="GT Cars Performance & Pricing",
        subtitle="Horsepower and MSRP across premium automobile manufacturers"
    )
    .tab_stubhead(label="Manufacturer")
    .tab_source_note("Price is the hero measure; horsepower is shown for reference as a related performance metric.")
    .tab_source_note("Source: GT Cars Dataset")
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px"
    )
)

# Apply Big Color to msrp (price) using heatmap helper
gt = heatmap(gt, "msrp", kind="sequential", hue="positive")

# Apply styling
gt = band(gt)
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
finalize(gt)
