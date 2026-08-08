import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

gt = (
    GT(df_display)
    .fmt_currency(columns='Price', currency='USD')
    .fmt_integer(columns='Horsepower')
)

gt.gtsave('table.png')
