import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()

# Sort by country, then by price (descending)
top10 = top10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Create table
gt_table = (
    GT(top10)
    .fmt_currency(columns='msrp', currency='USD')
    .cols_label(
        mfr='Manufacturer',
        model='Model',
        ctry_origin='Country',
        drivetrain='Drivetrain',
        trsmn='Transmission',
        msrp='MSRP'
    )
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
