import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Select relevant columns and create the table
table_df = df[['mfr', 'model', 'year', 'hp', 'msrp']].copy()
table_df = table_df.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'year': 'Year',
    'hp': 'Horsepower',
    'msrp': 'Price'
})

# Create the GT table
gt_table = (
    GT(table_df)
    .fmt_number(columns='Horsepower', decimals=0)
    .fmt_currency(columns='Price', currency='USD')
    .tab_header(
        title='GT Cars: Horsepower and Price'
    )
)

# Save to PNG
gt_table.gtsave('table.png')
