import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Select and rename columns
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price (MSRP)']

# Create the table
gt = (
    GT(df_display)
    .fmt_number(columns='Horsepower', decimals=0)
    .fmt_currency(columns='Price (MSRP)', currency='USD')
)

# Save as PNG
gt.gtsave('table.png')
print("Table saved to table.png")
