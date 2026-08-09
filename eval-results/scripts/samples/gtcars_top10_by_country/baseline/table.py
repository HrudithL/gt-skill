import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')

# Sort by MSRP descending and get top 10
top10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'drivetrain', 'trsmn', 'msrp', 'ctry_origin']].copy()

# Sort by country, then by MSRP descending
top10 = top10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Create display columns
top10['Car'] = top10['mfr'] + ' ' + top10['model'] + ' (' + top10['year'].astype(int).astype(str) + ')'
top10['Drivetrain'] = top10['drivetrain'].str.upper()
top10['Transmission'] = top10['trsmn']
top10['Price'] = '$' + (top10['msrp'] / 1000).round(1).astype(str) + 'K'
top10['Country'] = top10['ctry_origin']

display_df = top10[['Country', 'Car', 'Drivetrain', 'Transmission', 'Price']]

gt = (
    GT(display_df)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .tab_options(
        container_width='900px',
        table_layout='auto'
    )
    .cols_label(
        Country='Country',
        Car='Car',
        Drivetrain='Drivetrain',
        Transmission='Transmission',
        Price='Price'
    )
)

gt.gtsave('table.png')
