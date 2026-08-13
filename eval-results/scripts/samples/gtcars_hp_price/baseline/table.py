import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price (USD)']
df_display['Price (USD)'] = df_display['Price (USD)'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")

gt = (
    GT(df_display)
    .fmt_number(columns=['Horsepower'], decimals=0)
    .tab_header(
        title="GT Cars with Horsepower and Price"
    )
)

gt.gtsave("table.png")
