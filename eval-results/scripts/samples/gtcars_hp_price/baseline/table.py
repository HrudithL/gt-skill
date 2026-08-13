import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Select relevant columns
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price ($)']

# Create the table
gt = (
    GT(df_display)
    .fmt_number(columns=['Horsepower'], decimals=0)
    .fmt_currency(columns=['Price ($)'], currency='USD')
)

# Save to PNG
gt.gtsave('table.png')
