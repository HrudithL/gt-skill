import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap, stub_tint, stripe

# Read the data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and create display name
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display["car"] = df["mfr"] + " " + df["model"]
df_display = df_display[["car", "hp", "msrp"]].reset_index(drop=True)

# Build the table
gt = (
    GT(df_display, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("High-performance vehicles ranked by horsepower and MSRP"),
    )
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
)

# Apply house style formatting
gt = humanize_labels(
    gt,
    df_display,
    overrides={"hp": "Horsepower", "msrp": "MSRP"},
)

# Color the two measures: horsepower (sequential/neutral) and price (sequential/neutral)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply band styling with navy accent_tint
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Apply small-color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source note and hairlines
gt = (
    gt.tab_source_note(source_note="Source: provided dataset.")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
