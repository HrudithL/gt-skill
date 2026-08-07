import pandas as pd
from great_tables import GT
from great_tables.data import exibble

df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'msrp', 'ctry_origin', 'drivetrain', 'trsmn']].copy()

# Sort by country, then by MSRP descending
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Rename columns for display
top_10 = top_10.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'year': 'Year',
    'msrp': 'MSRP',
    'ctry_origin': 'Country',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission'
})

# Create GT table
gt = (
    GT(top_10)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .fmt_currency(columns='MSRP', currency='USD')
    .fmt_integer(columns='Year')
    .tab_options(
        column_labels_hidden=False,
    )
)

# Render to PNG
gt.gtsave('table.png')
print("Table rendered to table.png")
