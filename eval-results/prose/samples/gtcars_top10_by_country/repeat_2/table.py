import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

# Step 1: UNDERSTAND THE DATA & CLEAN
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top = df.nlargest(10, "msrp").copy()

# Select and rename columns for display
df_table = df_top[["ctry_origin", "mfr", "model", "msrp", "drivetrain", "trsmn"]].copy()
df_table.columns = ["Country", "Manufacturer", "Model", "Price", "Drivetrain", "Transmission"]

# Group by country
df_table = df_table.sort_values(["Country", "Price"], ascending=[True, False]).reset_index(drop=True)

# Step 2: ORGANIZE COLUMNS
# Country will be the groupname_col, Manufacturer/Model form the row identity
# Price is the hero measure (ordered magnitude, ≥5 rows) → gradient fill

# Step 3: BIG COLOR
# Price is a neutral magnitude (money) → Blues palette
# Compute domain from the price column
cols_price = ["Price"]
price_lo = float(np.nanmin(df_table[cols_price].to_numpy()))
price_hi = float(np.nanmax(df_table[cols_price].to_numpy()))

# Step 4 & 5: BUILD TABLE WITH STYLING
gt = (
    GT(df_table, groupname_col="Country")
    # Step 2: Format price (currency, 0 decimals per small_color.md)
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    # Step 3: Big Color — gradient fill on Price
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 5(a): Cell borders — body hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 4: Heading band — light tint since we have Big Color (Blues)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_text_transform="capitalize",
    )
    # Step 5(c): Row striping — 10 rows, body not fully filled by color → stripe required
    .opt_row_striping()
    # Step 5: Row-group emphasis (mandatory for groupname_col)
    .tab_options(
        row_group_background_color="#EAF0F6",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
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
    # Step 6: Titles & annotations
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission details",
    )
    # Step 5(f): Two footer notes (analytical caption + source)
    .tab_source_note(
        source_note="Price reflects manufacturer's suggested retail price (MSRP). Drivetrain classification: rwd (rear-wheel drive), awd (all-wheel drive), dd (direct drive). Transmission: a = automatic, m = manual."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv — global performance sports car database"
    )
)

# Render and save
gt.gtsave("table.png", expand=15)
print("✓ Table rendered to table.png")
