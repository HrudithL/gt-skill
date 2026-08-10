import pandas as pd
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Filter to get top 10 most expensive cars overall
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Rename columns for clarity
top_10.columns = ["Manufacturer", "Model", "Country", "Drivetrain", "Transmission", "Price"]

# Ensure Price is numeric and properly formatted
top_10["Price"] = pd.to_numeric(top_10["Price"], errors="coerce")

# Sort by Country, then by Price descending within each country
top_10 = top_10.sort_values(by=["Country", "Price"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table
gt = (
    GT(top_10, groupname_col="Country", rowname_col="Manufacturer")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    # Step 4: Heading band (dark since no Big Color)
    .tab_options(
        column_labels_background_color="#2C3E50",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5(a): Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
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
    # Step 5(d): Stub tint
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Step 5: Row group styling
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Step 5(e): Format Price column as currency
    .fmt_currency(columns="Price", decimals=0, currency="USD")
    # Step 6: Annotations
    .tab_source_note(source_note="Top 10 vehicles by MSRP price. Table groups cars by their country of manufacturing origin.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Render to PNG
gt.gtsave("table.png", expand=15)
