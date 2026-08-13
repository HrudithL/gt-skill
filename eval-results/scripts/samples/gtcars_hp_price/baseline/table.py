import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('gtcars.csv')

# Select relevant columns and rename for display
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price ($)']

# Format the table
gt = (
    GT(df_display)
    .fmt_number(columns='Horsepower', decimals=0)
    .fmt_currency(columns='Price ($)', currency='USD')
    .tab_header(title='GT Cars: Horsepower & Price')
)

gt.gtsave('table.png')
