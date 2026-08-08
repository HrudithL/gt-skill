import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')

# Sort by country and price (descending within country)
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Select relevant columns and rename for display
display_df = top_10[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Year', 'Country', 'Drivetrain', 'Transmission', 'MSRP']

# Format the MSRP column
display_df['MSRP'] = display_df['MSRP'].apply(lambda x: f"${x:,.0f}")

# Create the GT table
gt = (
    GT(display_df)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .tab_stubhead(label="")
    .cols_label(
        Manufacturer="Manufacturer",
        Model="Model",
        Year="Year",
        Country="Country",
        Drivetrain="Drivetrain",
        Transmission="Transmission",
        MSRP="MSRP"
    )
    .cols_align(align="center", columns=['Year', 'Drivetrain', 'Transmission'])
    .cols_align(align="right", columns=['MSRP'])
    .tab_options(
        container_width="100%"
    )
)

gt.gtsave("table.png")
