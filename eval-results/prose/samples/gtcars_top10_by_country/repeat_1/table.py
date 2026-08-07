import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

# Step 1: Clean and prepare data
df = pd.read_csv("gtcars.csv")

# Sort by price (descending) and take top 10
df_top10 = df.nlargest(10, "msrp").copy()

# Create a display name combining manufacturer and model
df_top10["name"] = df_top10["mfr"] + " " + df_top10["model"]

# Organize columns for display: country, name, drivetrain, transmission, price
df_display = df_top10[["ctry_origin", "name", "drivetrain", "trsmn", "msrp"]].copy()

# Rename columns for display
df_display.columns = ["Country", "Car", "Drivetrain", "Transmission", "Price"]

# Sort by country, then by price descending (for logical grouping)
df_display = df_display.sort_values(["Country", "Price"], ascending=[True, False]).reset_index(drop=True)

# Step 2: Create GT table with grouping and stub
gt = (
    GT(df_display, rowname_col="Car", groupname_col="Country")
    # Step 3: Big Color - price gradient
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[float(np.nanmin(df_display["Price"].to_numpy())),
                float(np.nanmax(df_display["Price"].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    # Step 5: Formatting
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    # Step 4: Light heading band (because we have Big Color)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # Washed light-blue tint
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Row group styling
    .tab_options(
        row_group_background_color="#EAF0F6",  # Washed light-blue to match band
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Frame border
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
    # Titles
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
)

# Render to PNG
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
