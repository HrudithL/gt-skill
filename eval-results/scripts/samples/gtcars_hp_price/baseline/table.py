import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']
df_display = df_display.sort_values('Horsepower', ascending=False)

gt = GT(df_display)
gt = gt.fmt_number(columns='Price', decimals=0)
gt = gt.tab_header(
    title='GT Cars',
    subtitle='Horsepower and Price'
)

gt.gtsave('table.png')
