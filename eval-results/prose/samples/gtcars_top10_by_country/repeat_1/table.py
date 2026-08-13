import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top10 = df.nlargest(10, "msrp").copy()

# Select and organize columns
df_top10 = df_top10[["ctry_origin", "model", "msrp", "drivetrain", "trsmn"]].copy()

# Rename columns for display
df_top10 = df_top10.rename(columns={
    "ctry_origin": "Country",
    "model": "Model",
    "msrp": "Price",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission"
})

# Sort by country then price descending for better grouping
df_top10 = df_top10.sort_values(["Country", "Price"], ascending=[True, False])

# Step 2: Calculate Big Color domain for price
price_cols = ["Price"]
price_lo = float(np.nanmin(df_top10[price_cols].to_numpy()))
price_hi = float(np.nanmax(df_top10[price_cols].to_numpy()))

# Step 3-7: Build the table with all styling
gt = (
    GT(df_top10, rowname_col="Model", groupname_col="Country")
    # Format price as currency (whole dollar)
    .fmt_currency(columns=["Price"], currency="USD", decimals=0, use_subunits=False)
    # Apply gradient fill to price (Big Color - Step 3)
    .data_color(
        columns=["Price"],
        palette="Blues",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    # Heading band (Step 4) - fixed branding band
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Small Color Polish (Step 5)
    # (a) Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (b) Column dividers - none needed (no spanners)
    # (c) Row striping - apply by default
    .opt_row_striping()
    # (d) Stub tint - fixed pale blue
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Formatting per column - drivetrain and transmission are text, already plain
    # (f) Titles & annotations (Step 6)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="By Country of Origin"
    )
    .tab_source_note(
        source_note="Includes drivetrain and transmission specifications for each vehicle."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
    # Row group styling - bold labels + structural rule
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Frame - boxed border on all sides
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
    # Compact layout - padding values
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Column widths to content
    .cols_width(cases={
        "Price": "140px",
        "Drivetrain": "120px",
        "Transmission": "120px",
    })
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
