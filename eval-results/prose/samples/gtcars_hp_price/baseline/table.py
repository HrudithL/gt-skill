import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')
df_display = df[['mfr', 'model', 'hp', 'msrp']].copy()
df_display.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']
df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
df_display['Horsepower'] = df_display['Horsepower'].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "N/A")

gt = (
    GT(df_display)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications across luxury and sports car manufacturers"
    )
)

gt.gtsave("table.png")
