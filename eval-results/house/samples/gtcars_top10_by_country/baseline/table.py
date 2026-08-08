import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv('gtcars.csv')

df_sorted = df.nlargest(10, 'msrp')

df_display = df_sorted[['ctry_origin', 'mfr', 'model', 'year', 'drivetrain', 'trsmn', 'msrp']].copy()
df_display = df_display.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])
df_display = df_display.reset_index(drop=True)

df_display.columns = ['Country', 'Manufacturer', 'Model', 'Year', 'Drivetrain', 'Transmission', 'MSRP']

df_display['MSRP'] = '$' + df_display['MSRP'].apply(lambda x: f'{x:,.0f}')

gt_table = (
    GT(df_display)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_label(
        Country="Country",
        Manufacturer="Manufacturer",
        Model="Model",
        Year="Year",
        Drivetrain="Drivetrain",
        Transmission="Transmission",
        MSRP="MSRP"
    )
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
