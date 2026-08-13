import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

gt = (
    GT(df_display)
    .fmt_integer(columns=['Horsepower'])
    .fmt_currency(columns=['Price'], currency='USD')
    .tab_header(
        title='GT Cars: Horsepower and Price'
    )
)

gt.gtsave('table.png')
