"""Top 10 most expensive GT cars, grouped by country of origin.

Data: ./gtcars.csv
Story: The 10 most expensive production cars, organized by their country of
       origin, with drivetrain and transmission details highlighted.
"""
import pandas as pd
from great_tables import GT, loc, style

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Ensure msrp is numeric (should already be, but validate)
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Sort by MSRP descending and take top 10
top10 = df.nlargest(10, "msrp").copy()

# Organize and prepare columns
top10 = top10[["mfr", "model", "msrp", "ctry_origin", "drivetrain", "trsmn", "year"]]
top10 = top10.reset_index(drop=True)
top10["rank"] = top10.index + 1

# Reorder columns for display
top10 = top10[["rank", "mfr", "model", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]]

# Create the GT table with grouping by country
gt = (
    GT(top10, groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Production cars ranked by MSRP, grouped by country of origin",
    )
    .cols_label(
        rank="#",
        mfr="Manufacturer",
        model="Model",
        year="Year",
        ctry_origin="Country",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        msrp="MSRP",
    )
    # Step 5: Format columns
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["year"], use_seps=False)
    # Step 5: Row striping (≥10 rows gate satisfied)
    .opt_row_striping()
    # Step 5: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Row group emphasis
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Step 4: Heading band (no Big Color, so dark DA solid with white text)
    .tab_options(
        column_labels_background_color="#22384F",
    )
    .tab_style(
        style=style.text(color="#FFFFFF", weight="bold"),
        locations=loc.column_labels(),
    )
    # Step 5: Frame border (all four sides)
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
    # Step 6: Source note (computational choice: selection by MSRP)
    .tab_source_note(
        source_note="Source: gtcars dataset (Posit / great_tables sample data)."
    )
)

# Render to PNG
gt.gtsave("table.png", expand=15)
