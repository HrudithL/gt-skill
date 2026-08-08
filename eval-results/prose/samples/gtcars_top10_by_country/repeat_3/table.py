import pandas as pd
from great_tables import GT, loc, style

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Step 1: Filter to only GT cars (cars with "GT" in model name)
gt_cars = df[df["model"].str.contains("GT", case=False, na=False)].copy()

# Sort by MSRP descending and take top 10
top10 = gt_cars.nlargest(10, "msrp").reset_index(drop=True)

# Compose a single human-readable car label
top10["car"] = top10["mfr"] + " " + top10["model"]

# Select and organize columns for display
display_cols = ["car", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]
top10 = top10[display_cols]

# Create the table
gt = (
    GT(top10, rowname_col="car", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin, with drivetrain and transmission details",
    )
    .cols_label(
        car="Car",
        year="Year",
        ctry_origin="Country",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        msrp="MSRP",
    )
    # Formatting per column type
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["year"], use_seps=False)
    .sub_missing(columns=["msrp", "year", "drivetrain", "trsmn"], missing_text="—")
    # Step 4: Heading band — no Big Color, so use dark Navy band with white text
    .tab_options(
        column_labels_background_color="#22384F",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish checklist
    # (a) Cell borders — hairline between all body rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping — ≥10 rows and no Big Color, so apply stripes
    .opt_row_striping()
    # (d) Stub tint — grey default
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Row group emphasis — required for grouped tables
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Frame borders — all four sides plus margin
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
    # Column alignment
    .cols_align(align="left", columns=["car", "ctry_origin", "drivetrain", "trsmn"])
    .cols_align(align="right", columns=["year", "msrp"])
    # Step 6: Titles, caption, and source note
    .tab_source_note(
        source_note="Source: gtcars dataset (Posit / great_tables sample data)."
    )
)

gt.gtsave("table.png", expand=15)
