import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')

df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']
df_display = df_display.reset_index(drop=True)

gt_table = (
    GT(df_display)
    .fmt_currency(columns='Price', currency='USD')
    .fmt_number(columns='Horsepower', decimals=0)
    .tab_header(
        title='GT Cars: Horsepower and Price',
        subtitle='A selection of high-performance vehicles'
    )
)

gt_table.gtsave('table.png')
