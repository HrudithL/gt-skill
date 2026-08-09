import pandas as pd
from great_tables import GT, style, loc

# Step 1: Read and clean data
df = pd.read_csv("gtcars.csv")

# Select top 10 by MSRP
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()

# Sort by country, then by MSRP descending within each country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Step 2: Organize columns
# Stub: mfr (manufacturer)
# Group: ctry_origin (country of origin)
# Measures: msrp (price), drivetrain, transmission

# Rename columns for display
top_10 = top_10.rename(columns={
    "mfr": "Manufacturer",
    "model": "Model",
    "ctry_origin": "Country",
    "msrp": "Price",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission"
})

# Step 3: No Big Color (categorical/text table)
# Step 4: Dark heading band (no Big Color)
# Step 5: Small Color polish

gt = (
    GT(top_10, rowname_col="Manufacturer", groupname_col="Country")
    # Frame border (Global constant)
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
    # Dark heading band (Step 4 - no Big Color)
    .tab_options(
        column_labels_background_color="#22384F",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Body row hairlines (Step 5a)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Row striping (Step 5c - ≥10 rows, not fully filled by Big Color)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Row group emphasis (Step 5 - grouping present)
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Stub tint (Step 5d)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Format currency column (Step 5e)
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    # Titles and annotations (Step 6)
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country of Origin",
        subtitle="Vehicle specifications including drivetrain and transmission details"
    )
    # Two separate footer notes (analytical caption + source note, Step 5f)
    .tab_source_note(source_note="Table shows the highest-priced vehicles in the dataset, grouped by country of origin.")
    .tab_source_note(source_note="Data source: gtcars.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
