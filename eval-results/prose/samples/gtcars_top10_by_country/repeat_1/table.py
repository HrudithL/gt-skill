"""Top 10 most expensive GT cars by country of origin.

Story: Expensive production cars grouped by their country of origin,
       showing drivetrain and transmission details alongside price.
"""
import pandas as pd
from great_tables import GT, loc, style

# STEP 1: DATA CLEANING — understand and validate
df = pd.read_csv("./gtcars.csv")

# Ensure msrp is numeric (already is from CSV read, but validate)
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Get top 10 most expensive cars globally
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by msrp descending within each country for better grouping
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a composite car name (mfr + model)
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Select and order columns for display
display_cols = [
    "car",
    "year",
    "ctry_origin",
    "msrp",
    "drivetrain",
    "trsmn",
]

top_10_display = top_10[display_cols].copy()

# STEP 2: ORGANIZE COLUMNS
# Trigger: user requested grouping by country → use groupname_col
# Trigger: no stub identifier needed here (car is a value column, not a row label)

gt = (
    GT(top_10_display, groupname_col="ctry_origin")
    .cols_label(
        car="Car",
        year="Year",
        ctry_origin="Country",
        msrp="MSRP",
        drivetrain="Drivetrain",
        trsmn="Transmission",
    )
    .cols_align(align="left", columns=["car", "drivetrain", "trsmn"])
    .cols_align(align="right", columns=["year", "msrp"])
)

# STEP 3: BIG COLOR
# Decision: No magnitude/gradient story here. Price is a display value, not a colored measure.
# This is a pure categorical table grouped by country with no Big Color treatment.

# STEP 4: HEADING BAND
# Decision: No Big Color → use DARK saturated band
# DA hue-selection rule: no gradient/heatmap, data subject is automotive/price → use default Navy

gt = gt.tab_options(
    column_labels_background_color="#22384F",        # Dark Academia Navy
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# STEP 5: SMALL-COLOR POLISH CHECKLIST

# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Column-group vertical dividers — no spanners, so skip

# (c) Row striping — ≥5 rows and no Big Color → apply
gt = gt.opt_row_striping()

# (d) Stub tint — no stub column, skip

# (e) Formatting per column
gt = (
    gt.fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["year"], use_seps=False)
    .sub_missing(columns=["car", "year", "ctry_origin", "msrp", "drivetrain", "trsmn"], missing_text="—")
)

# Row-group emphasis (grouped by country)
# Gate: groupname_col is set → apply light fill + bold
gt = gt.tab_options(
    row_group_background_color="#F0F0F0",
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# STEP 6: TITLES & ANNOTATIONS

gt = (
    gt.tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin, showing drivetrain and transmission",
    )
    .tab_source_note(source_note="Source: gtcars dataset (Posit / great_tables sample data).")
)

# STEP 7: FRAME & RENDER

# Frame: light border on all four sides + margin
gt = gt.tab_options(
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

# Render with expansion margin
gt.gtsave("table.png", expand=15)
