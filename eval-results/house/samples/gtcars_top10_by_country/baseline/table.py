import pandas as pd
from great_tables import GT, loc, style

# Read the CSV file
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']].copy()

# Sort by country, then by price descending
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Rename columns for display
display_df = top_10_sorted.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'ctry_origin': 'Country',
    'msrp': 'Price',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission'
})

# Format price as currency
display_df['Price'] = display_df['Price'].apply(lambda x: f'${x:,.0f}')

# Create the table
gt = (
    GT(display_df)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .cols_label(
        Manufacturer='Manufacturer',
        Model='Model',
        Country='Country',
        Price='MSRP',
        Drivetrain='Drivetrain',
        Transmission='Transmission'
    )
    .tab_options(table_width='100%')
)

# Save as PNG
gt.gtsave('table.png')
print("Table saved as table.png")
