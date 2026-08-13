import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, humanize_labels

df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp").copy()

# Create display columns
top10["car"] = top10["mfr"] + " " + top10["model"]
top10["price"] = top10["msrp"]

# Reorder and select columns for display
display_cols = ["car", "ctry_origin", "price", "drivetrain", "trsmn"]
display_df = top10[display_cols].reset_index(drop=True)
display_df = display_df.rename(columns={
    "car": "car",
    "ctry_origin": "country",
    "price": "msrp",
    "drivetrain": "drivetrain",
    "trsmn": "transmission"
})

# Sort by country then price descending for better grouping
display_df = display_df.sort_values(["country", "msrp"], ascending=[True, False]).reset_index(drop=True)

gt = (
    GT(display_df, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By price, grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car")
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "msrp": "MSRP",
        "country": "Country",
        "drivetrain": "Drivetrain",
        "transmission": "Transmission"
    },
)

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "180px",
        "country": "130px",
        "msrp": "120px",
        "drivetrain": "100px",
        "transmission": "100px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Color the price column with sequential heatmap
from house_table import heatmap
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply house formatting
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

from house_table import group_emphasis
gt = group_emphasis(gt)

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Ranked by MSRP (manufacturer's suggested retail price) in descending order."
    )
    .tab_source_note(source_note="Source: gtcars.csv dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
