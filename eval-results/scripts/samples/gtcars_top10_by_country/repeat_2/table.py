import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, band, stripe, stub_tint, frame, finalize, heatmap

df = pd.read_csv("gtcars.csv")

# Step 1: Data cleaning
df = df[["mfr", "model", "msrp", "drivetrain", "trsmn", "ctry_origin"]].copy()
df = df.dropna(subset=["msrp"])

# Sort by price and take top 10, then sort by country for grouping
df_top10 = df.nlargest(10, "msrp").sort_values("ctry_origin")

# Create display column combining manufacturer and model for better readability
df_top10["Model"] = df_top10["mfr"] + " " + df_top10["model"]
df_top10 = df_top10.drop(columns=["mfr", "model"])

# Rename columns for display
df_top10 = df_top10.rename(columns={
    "msrp": "Price",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "ctry_origin": "Country"
})

# Reorder and set Model as the stub column
df_top10 = df_top10[["Country", "Model", "Drivetrain", "Transmission", "Price"]]
df_top10 = df_top10.set_index("Model")

# Step 2: Organize with grouping and stub
gt = GT(df_top10, groupname_col="Country")

# Step 3: Big Color - price heatmap (sequential Blues)
gt = heatmap(gt, "Price", kind="sequential", hue="neutral")

# Format the price column
gt = gt.fmt_currency(columns="Price", decimals=0, use_seps=True)

# Step 4: Heading band (fixed navy, bold labels, white text)
gt = band(gt)

# Step 5: Small Color polish - all the fixed checklist items
# Row striping (fixed neutral grey)
gt = stripe(gt)

# Stub tint (fixed pale blue)
gt = stub_tint(gt)

# Cell borders and column-label bottom rule
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# Column widths for compact layout
gt = gt.cols_width(cases={
    "Drivetrain": "100px",
    "Transmission": "110px",
    "Price": "120px",
})

# Padding for compact layout
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="8px",
)

# Frame (boxed border on all sides)
gt = frame(gt)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .tab_source_note(source_note="Price shown in USD MSRP, highest to lowest within each country group.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Finalize with render parameters
finalize(gt)
