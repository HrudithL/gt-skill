import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE,
    frame,
    finalize,
    band,
    stub_tint,
    heatmap,
    group_emphasis,
    humanize_labels,
)

# Read the data and filter to top 10 most expensive cars
df = pd.read_csv("gtcars.csv")

# Select top 10 by MSRP
top10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Sort by country, then by price (descending) for better grouping
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Rename columns for display
top10.columns = ["manufacturer", "model", "country_origin", "drivetrain", "transmission", "msrp"]

# Create GT table with country as grouping
gt = (
    GT(top10, rowname_col="manufacturer", groupname_col="country_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By manufacturer and country of origin, with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Manufacturer")
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
)

gt = humanize_labels(
    gt,
    top10,
    overrides={
        "country_origin": "Country of Origin",
        "msrp": "MSRP",
    },
)

# Single colored measure: MSRP as sequential neutral (Blues)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Heading band with navy accent_tint
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Stub tint and group emphasis
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Frame and source note
gt = gt.tab_source_note(source_note="Source: gtcars.csv dataset.")
gt = frame(gt)

# Finalize with defaults
finalize(gt, path="table.png", zoom=2.0, expand=15)
