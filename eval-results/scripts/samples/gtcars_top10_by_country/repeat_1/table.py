"""Top 10 most expensive GT cars grouped by country of origin.

Data: gtcars.csv
Story: Top 10 cars by MSRP, grouped by country, with drivetrain and transmission.
"""
import numpy as np
import pandas as pd
from great_tables import GT, loc, style

# Step 1: Read and clean data
df = pd.read_csv("gtcars.csv")

# Ensure MSRP is numeric
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Get top 10 by MSRP
top10 = df.nlargest(10, "msrp").reset_index(drop=True)

# Create composite car label
top10["car"] = top10["mfr"] + " " + top10["model"]

# Sort by country and then by MSRP descending within each country
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Select and arrange columns
top10 = top10[["car", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]]

# Step 2: Organize columns with grouping by country
# Compute color domain for MSRP (ordered magnitude)
lo = float(np.nanmin(top10["msrp"].to_numpy()))
hi = float(np.nanmax(top10["msrp"].to_numpy()))

gt = (
    # Grouping by country — mandatory per user prompt
    GT(top10, rowname_col="car", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin, ranked by MSRP",
    )
    .cols_label(
        car="Car",
        year="Year",
        ctry_origin="Country",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        msrp="MSRP",
    )
    # Step 5: Formatting per column
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["year"], use_seps=False)
    # Step 3: Big Color — MSRP gets a sequential gradient (ordered magnitude, ≥5 rows)
    .data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band — fixed branding navy
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Step 5 (a): Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5 (d): Stub tint
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Step 5 (c): Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5: Row group emphasis (bold + structural rule)
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Column alignment
    .cols_align(align="left", columns=["car", "ctry_origin", "drivetrain", "trsmn"])
    .cols_align(align="right", columns=["year", "msrp"])
    # Step 5 (g): Compact layout — cols_width + pinned padding
    .cols_width(cases={
        "car": "200px",
        "year": "70px",
        "ctry_origin": "120px",
        "drivetrain": "95px",
        "trsmn": "110px",
        "msrp": "130px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame (all four sides)
    .tab_options(
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Step 6: Titles & annotations — two-call footer convention
    .tab_source_note(
        source_note="MSRP values displayed with sequential color gradient (Blues) indicating magnitude across all cars."
    )
    .tab_source_note(source_note="Source: gtcars dataset.")
)

gt.gtsave("table.png", zoom=2.0, expand=15)
