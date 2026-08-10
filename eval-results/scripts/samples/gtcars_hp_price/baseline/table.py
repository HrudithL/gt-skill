import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_table = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_table.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

gt = (
    GT(df_table)
    .fmt_currency(columns='Price', currency='USD')
    .cols_label(
        Horsepower='Horsepower (hp)',
        Price='MSRP'
    )
    .tab_header(
        title='GT Cars',
        subtitle='Horsepower and Price'
    )
)

gt.gtsave('table.png')
