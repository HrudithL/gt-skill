import pandas as pd
from great_tables import GT
from great_tables.data import exibble

df = pd.read_csv('./gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')

# Sort by country then by price descending for better presentation
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Rename transmission code to human readable format
trsmn_map = {
    '6m': '6-Speed Manual',
    '6a': '6-Speed Auto',
    '7m': '7-Speed Manual',
    '7a': '7-Speed Auto',
    '8a': '8-Speed Auto',
    '8am': '8-Speed Auto/Manual',
    '9a': '9-Speed Auto',
    '1dd': '1-Speed Direct Drive'
}

top_10_sorted['transmission'] = top_10_sorted['trsmn'].map(trsmn_map)

# Create a new dataframe with relevant columns
display_df = top_10_sorted[[
    'ctry_origin',
    'mfr',
    'model',
    'year',
    'drivetrain',
    'transmission',
    'msrp'
]].copy()

display_df.columns = ['Country', 'Manufacturer', 'Model', 'Year', 'Drivetrain', 'Transmission', 'Price (USD)']

# Convert price to string with formatting
display_df['Price (USD)'] = display_df['Price (USD)'].apply(lambda x: f'${x:,.0f}')

# Create the table
gt = (
    GT(display_df)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .tab_style(
        style=['background-color: #f0f0f0'],
        locations=[],
    )
    .opt_row_striping()
)

gt.gtsave('table.png')
print("Table saved to table.png")
