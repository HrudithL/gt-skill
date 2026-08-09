import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, finalize, band, stripe, stub_tint,
    group_emphasis, humanize_labels, heatmap
)

# Read the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by price (descending within each country)
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create display columns
top10["Model"] = top10["mfr"] + " " + top10["model"]
top10["Drivetrain"] = top10["drivetrain"].str.upper()
top10["Transmission"] = top10["trsmn"]
top10["Price"] = top10["msrp"]

# Select columns for display
display_df = top10[["Model", "Drivetrain", "Transmission", "Price", "ctry_origin"]].copy()
display_df.columns = ["model", "drivetrain", "transmission", "price", "ctry_origin"]

# Build the table
gt = (
    GT(display_df, rowname_col="model", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By MSRP, grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Model")
    .fmt_currency(columns="price", decimals=0)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# Apply humanize_labels
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "price": "MSRP",
        "ctry_origin": "Country",
    },
)

# Color the MSRP column (sequential heatmap - neutral/Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Apply band styling
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Apply small-color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: gtcars dataset. MSRP in USD.")

# Frame and finalize
gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
