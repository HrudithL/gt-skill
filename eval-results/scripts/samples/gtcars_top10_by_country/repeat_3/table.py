import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

# Step 1: Data cleaning
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")
df["ctry_origin"] = df["ctry_origin"].str.strip()

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["model", "mfr", "ctry_origin", "msrp", "drivetrain", "trsmn"]].reset_index(drop=True)

# Rename columns for display
top_10 = top_10.rename(columns={
    "model": "Model",
    "mfr": "Manufacturer",
    "ctry_origin": "Country",
    "msrp": "Price",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission"
})

# Sort by price descending for consistent display
top_10 = top_10.sort_values("Price", ascending=False).reset_index(drop=True)

# Step 2: Organize columns - use country as groupname_col, manufacturer as stub
gt = GT(
    top_10,
    rowname_col="Manufacturer",
    groupname_col="Country"
)

# Step 3: Big Color — highlight top 3 rows
top_3_indices = [0, 1, 2]
gt = gt.tab_style(
    style=[style.fill(color="#9A7B33"), style.text(color="#ffffff", weight="bold")],
    locations=loc.body(rows=top_3_indices),
)

# Step 4: Column labels and header band
gt = gt.cols_label(
    Model="Model",
    Manufacturer="Manufacturer",
    Country="Country",
    Price="Price (USD)",
    Drivetrain="Drivetrain",
    Transmission="Transmission"
)

gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by Country of Origin with Drivetrain & Transmission Details"
)

# Step 5: Small Color polish - formatting
gt = gt.fmt_currency(
    columns="Price",
    currency="USD",
    decimals=0,
    use_seps=True
)

# Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Stub tint
gt = gt.tab_style(
    style=style.fill(color="#F0F0F0"),
    locations=loc.stub(),
)

# Row group styling
gt = gt.tab_options(
    row_group_background_color="#F0F0F0",
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# Row striping
gt = gt.opt_row_striping()

# Frame and border
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

# Render
gt.gtsave("table.png", expand=15)
