import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Select and format the columns we need
table_df = df[['mfr', 'model', 'hp', 'msrp']].copy()
table_df.columns = ['Manufacturer', 'Model', 'Horsepower', 'MSRP']

# Create and style the GT table
gt = (
    GT(table_df)
    .fmt_number(columns=['Horsepower'], decimals=0)
    .fmt_currency(columns=['MSRP'], currency='USD')
    .tab_header(
        title='GT Cars: Horsepower and Price'
    )
)

gt.gtsave('table.png')
