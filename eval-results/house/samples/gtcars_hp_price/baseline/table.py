import pandas as pd
import great_tables as gt

df = pd.read_csv('gtcars.csv')

# Select relevant columns and create display names
display_df = df[['mfr', 'model', 'hp', 'msrp']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price ($)']

# Format and create the table
gt_table = (
    gt.GT(display_df)
    .fmt_integer(columns=['Horsepower'])
    .fmt_currency(columns=['Price ($)'], currency='USD')
    .tab_header(
        title='GT Cars Database',
        subtitle='Horsepower and Price'
    )
)

gt_table.gtsave('table.png')
