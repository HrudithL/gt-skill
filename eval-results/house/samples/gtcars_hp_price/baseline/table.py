import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('gtcars.csv')

# Select only the columns we need
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

# Create the GT table
gt = (
    GT(df_display)
    .fmt_integer(columns='Horsepower')
    .fmt_currency(columns='Price', currency='USD')
    .tab_header(title='GT Cars - Horsepower & Price')
)

# Save as PNG
gt.gtsave("table.png")
