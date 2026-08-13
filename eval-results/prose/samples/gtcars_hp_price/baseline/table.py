import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('./gtcars.csv')

# Select and format the columns we need
table_data = df[['mfr', 'model', 'hp', 'msrp']].copy()
table_data.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

# Create the table
gt = (
    GT(table_data)
    .fmt_number(columns='Horsepower', decimals=0)
    .fmt_currency(columns='Price', currency='USD', decimals=0)
    .cols_align(align='center')
)

# Save the table
gt.gtsave('table.png')
