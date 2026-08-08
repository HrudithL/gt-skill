import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("./gtcars.csv")

# Convert MSRP to numeric (already numeric but ensure float type)
df["msrp"] = df["msrp"].astype(float)

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Sort by country, then by price descending
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Rename columns for display
top10 = top10.rename(columns={
    "mfr": "Manufacturer",
    "model": "Model",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP"
})

# Step 2: Create the GT table with grouping by country
gt = (
    GT(top10, rowname_col="Manufacturer", groupname_col="Country")
    # Step 3: Color the MSRP column (ordered magnitude, ≥5 rows, sequential palette for neutral money magnitude)
    .fmt_currency(columns="MSRP", currency="USD", decimals=0, use_seps=True)
    .data_color(
        columns="MSRP",
        palette="Blues",
        domain=[float(np.nanmin(top10[["MSRP"]].to_numpy())), float(np.nanmax(top10[["MSRP"]].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - light band because we have Big Color (Blues)
    .tab_options(
        heading_background_color="#EAF0F6",
        column_labels_background_color="#EAF0F6",
        column_labels_text_transform="uppercase",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    .tab_options(
        # Cell borders - light hairline between rows
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Frame border
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
        # Row striping (≥10 rows and body not fully filled by Big Color)
        row_striping_background_color="#F6F6F6",
        # Stub tint - use washed-DA tint matching Blues
        stub_background_color="#EAF0F6",
        # Row group styling
        row_group_background_color="#EAF0F6",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Add structural borders on group boundaries
    .tab_style(
        style=style.borders(sides="top", color="#BDBDBD", weight="1.5px"),
        locations=loc.body(rows=[i for i in range(1, len(top10)) if top10.iloc[i]["Country"] != top10.iloc[i-1]["Country"]]),
    )
    # Step 6: Titles and annotations
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain and Transmission Details"
    )
    .tab_source_note(source_note="Source: gtcars.csv dataset")
)

# Render to PNG
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
