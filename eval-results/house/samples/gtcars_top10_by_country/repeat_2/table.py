"""Top 10 Most Expensive GT Cars by Country"""

import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, finalize, stripe, stub_tint, group_emphasis, humanize_labels

# Read the data and filter to top 10 most expensive
df = pd.read_csv("gtcars.csv")
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].reset_index(drop=True)
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table with country grouping
gt = (
    GT(top_10, rowname_col="model", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Ranked by MSRP, grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Model")
    .tab_spanner(label="Specifications", columns=["drivetrain", "trsmn"])
    .fmt_currency(columns="msrp", decimals=0, currency="USD")
    .fmt_integer(columns="year")
    .sub_missing(columns=["drivetrain", "trsmn"], missing_text="—")
)

gt = humanize_labels(
    gt,
    top_10,
    overrides={
        "mfr": "Manufacturer",
        "year": "Year",
        "drivetrain": "Drivetrain",
        "trsmn": "Transmission",
        "ctry_origin": "Country",
        "msrp": "MSRP",
    },
)

# Apply Big Color: color the MSRP column as the sequential hero measure (Blues/neutral)
gt = gt.data_color(
    columns="msrp",
    palette="Blues",
    domain=[top_10["msrp"].min(), top_10["msrp"].max()],
    na_color=PALETTE["neutral"]["na_cell"],
    truncate=False,
    autocolor_text=True,
)

# Apply house-format styling
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: gtcars.csv dataset. MSRP shown in USD.")

# Finalize and render
finalize(gt, path="table.png", zoom=2.0, expand=15)
