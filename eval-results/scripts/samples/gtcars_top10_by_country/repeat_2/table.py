import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

# Step 1: Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Create display label combining manufacturer and model
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Select and organize columns
display_df = top_10[["car", "drivetrain", "trsmn", "msrp", "ctry_origin"]].copy()
display_df = display_df.rename(columns={
    "car": "Car",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP",
    "ctry_origin": "Country"
})

# Reorder for display (country as grouping, then car details, price at the edge)
display_df = display_df[["Country", "Car", "Drivetrain", "Transmission", "MSRP"]]

# Data-driven domain for MSRP
cols_msrp = ["MSRP"]
lo = float(np.nanmin(display_df[cols_msrp].to_numpy()))
hi = float(np.nanmax(display_df[cols_msrp].to_numpy()))

# Build the table
gt = (
    GT(display_df, groupname_col="Country", rowname_col="Car")
    .fmt_currency(columns="MSRP", decimals=0, currency="USD")
    .data_color(
        columns="MSRP",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .tab_source_note(
        source_note="The 10 highest-priced vehicles, grouped by country of origin and sorted within each country by MSRP."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = (
    gt.tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_options(
        row_striping_background_color="#F6F6F6",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
)

# Compact layout
gt = gt.cols_width(cases={
    "Car": "180px",
    "Drivetrain": "100px",
    "Transmission": "110px",
    "MSRP": "140px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Frame and finalize
gt = frame(gt)
gt = finalize(gt)

gt.gtsave("table.png")
