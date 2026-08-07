import pandas as pd
from great_tables import GT, style, loc

# Step 1: Read and clean the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars overall
top_10_expensive = df.nlargest(10, "msrp").copy()

# Sort by country, then by price (descending)
top_10_expensive = top_10_expensive.sort_values(
    by=["ctry_origin", "msrp"], ascending=[True, False]
)

# Select relevant columns: country, model, drivetrain, transmission, price
display_df = top_10_expensive[[
    "ctry_origin", "mfr", "model", "drivetrain", "trsmn", "msrp"
]].reset_index(drop=True)

# Rename columns for display
display_df = display_df.rename(columns={
    "ctry_origin": "Country",
    "mfr": "Manufacturer",
    "model": "Model",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "Price"
})

# Step 2: Create GT with grouping by country
gt = GT(
    display_df,
    groupname_col="Country",
    rowname_col=None
)

# Step 3: Big Color - highlight top 3 most expensive cars overall
top_3_indices = display_df.nlargest(3, "Price").index.tolist()

# Step 4: Heading band - dark band (Navy) since we have Big Color
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by country of origin, with drivetrain and transmission details"
)

# Step 5: Small Color polish and formatting

# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Heading band - dark Navy
gt = gt.tab_options(
    column_labels_background_color="#22384F",
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Row group emphasis
gt = gt.tab_options(
    row_group_background_color="#F0F0F0",
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# (c) Row striping (≥10 rows with no full body Big Color)
gt = gt.opt_row_striping()

# (e) Formatting per column
gt = gt.fmt_currency(columns="Price", currency="USD", decimals=0)

# Apply Big Color highlight to top 3 rows
gt = gt.tab_style(
    style=[
        style.fill(color="#9A7B33"),
        style.text(color="#ffffff", weight="bold")
    ],
    locations=loc.body(rows=top_3_indices)
)

# Add source note
gt = gt.tab_source_note(
    "Data includes the top 10 most expensive GT cars by MSRP. Top 3 highlighted."
)

# Frame and render
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

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table saved to table.png")
