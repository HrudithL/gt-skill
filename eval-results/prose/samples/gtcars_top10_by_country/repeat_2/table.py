import pandas as pd
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'msrp', 'drivetrain', 'trsmn', 'ctry_origin']].copy()

# Sort by country, then by MSRP descending for display within groups
top10 = top10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Ensure msrp is numeric
top10['msrp'] = pd.to_numeric(top10['msrp'], errors='coerce')

# Step 2: Organize columns
# Create display columns with better names
top10['Car'] = top10['mfr'] + ' ' + top10['model']
top10['Drivetrain'] = top10['drivetrain'].str.upper()
top10['Transmission'] = top10['trsmn'].str.upper()
top10['Price'] = top10['msrp']

# Select and order columns for display, with country as grouping column
display_df = top10[['ctry_origin', 'Car', 'Drivetrain', 'Transmission', 'Price']].copy()
display_df.columns = ['Country', 'Car', 'Drivetrain', 'Transmission', 'Price']

# Step 3: Build the table with grouping
gt = (
    GT(display_df, groupname_col='Country', rowname_col='Car')

    # Step 4: Heading band - no Big Color, so use dark saturated band (Navy)
    .tab_options(
        column_labels_background_color="#22384F",        # Navy Dark Academia solid
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )

    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )

    # Step 5d: Stub tint (row identifier column)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )

    # Step 5e: Format currency column (Price)
    .fmt_currency(columns='Price', currency='USD', decimals=0, use_seps=True)

    # Step 5: Row-group emphasis (grouping header styling)
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )

    # Frame - boxed border
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

    # Titles and annotations
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain and Transmission Details"
    )
)

# Render to PNG
gt.gtsave("table.png", expand=15)
