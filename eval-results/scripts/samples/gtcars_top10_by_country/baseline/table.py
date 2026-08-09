import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']].copy()

# Sort by country, then by price descending
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Rename columns for display
top_10_sorted = top_10_sorted.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'year': 'Year',
    'ctry_origin': 'Country',
    'msrp': 'Price',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission'
})

# Format the price column as currency
top_10_sorted['Price'] = top_10_sorted['Price'].apply(lambda x: f'${x:,.0f}')

# Create the GT table
gt = (
    GT(top_10_sorted)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin with Drivetrain & Transmission Details'
    )
    .tab_options(
        container_width='100%'
    )
)

# Save as PNG
gt.gtsave('table.png')
print("Table saved to table.png")
