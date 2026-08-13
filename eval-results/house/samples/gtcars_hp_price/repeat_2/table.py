import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the CSV data
df = pd.read_csv("gtcars.csv")

# Select columns for the table and sort by horsepower descending
df_table = df[["mfr", "model", "hp", "msrp"]].copy()
df_table["car"] = df_table["mfr"] + " " + df_table["model"]
df_table = df_table[["car", "hp", "msrp"]].sort_values("hp", ascending=False).reset_index(drop=True)

# Create the GT table
gt = (
    GT(df_table, rowname_col="car")
    .tab_header(
        title="GT Cars Performance Overview",
        subtitle=md("Horsepower and price for high-performance vehicles"),
    )
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    df_table,
    overrides={"hp": "Horsepower", "msrp": "Price"},
)

# Apply formatting
gt = gt.cols_width(cases={"car": "220px", "hp": "120px", "msrp": "120px"})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap coloring to horsepower (the primary measure)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

# Apply styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = hairlines(gt)
gt = frame(gt)

# Add source notes
gt = gt.tab_source_note(
    source_note="Horsepower shown at maximum RPM."
)
gt = gt.tab_source_note(
    source_note="Source: GT Cars dataset.",
)

# Finalize and save
finalize(gt)
