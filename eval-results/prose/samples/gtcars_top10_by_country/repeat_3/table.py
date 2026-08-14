import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Remove rows with missing MSRP
df = df.dropna(subset=["msrp"])

# Get top 10 most expensive cars overall
top_10 = df.nlargest(10, "msrp").copy()

# Create a composite car identifier
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Rename transmission codes to readable format
transmission_names = {
    "6a": "6-Auto",
    "6m": "6-Manual",
    "7a": "7-Auto",
    "7m": "7-Manual",
    "8a": "8-Auto",
    "8am": "8-Auto",
    "9a": "9-Auto",
    "1dd": "1-Direct",
}
top_10["transmission"] = top_10["trsmn"].map(transmission_names)

# Capitalize drivetrain
top_10["drivetrain"] = top_10["drivetrain"].str.upper()

# Sort by country, then by MSRP descending
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and rename columns for display
display_df = top_10[["car", "ctry_origin", "drivetrain", "transmission", "msrp"]].copy()
display_df.columns = ["Car", "Country", "Drivetrain", "Transmission", "Price"]

# Step 2: Organize columns
# Car is the stub, Country is the grouping dimension, Price is the hero measure

# Step 3: Big Color - color the Price column (ordered magnitude, qualifies)
lo = float(np.nanmin(display_df[["Price"]].to_numpy()))
hi = float(np.nanmax(display_df[["Price"]].to_numpy()))

# Step 4 & 5: Build the table with heading band and polish
gt = (
    GT(display_df, rowname_col="Car", groupname_col="Country")
    # Format Price as currency
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    # Step 3: Color the Price column
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed branding constants)
    .tab_options(
        heading_title_font_size="16px",
        heading_subtitle_font_size="13px",
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_background_color="#08306B",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Column label bottom rule
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.body(columns="Car"),
    )
    # Row-group emphasis (bold + structural rule)
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Frame border (all four sides)
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
    # Compact layout
    .cols_width(cases={
        "Car": "200px",
        "Drivetrain": "100px",
        "Transmission": "110px",
        "Price": "120px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 6: Titles & annotations
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin",
    )
    .tab_source_note("Price reflects MSRP in USD; values are manufacturer's suggested retail prices.")
    .tab_source_note("Data source: gtcars.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
