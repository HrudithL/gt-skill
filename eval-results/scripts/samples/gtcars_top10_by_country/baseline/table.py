import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].reset_index(drop=True)

# Sort by country, then by price (descending)
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Create GT table
gt = (
    GT(top_10_sorted)
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .cols_label(
        mfr='Manufacturer',
        model='Model',
        ctry_origin='Country',
        drivetrain='Drivetrain',
        trsmn='Transmission',
        msrp='MSRP ($)'
    )
    .fmt_currency(columns='msrp', currency='USD')
    .cols_width(
        mfr='150px',
        model='150px',
        ctry_origin='150px',
        drivetrain='100px',
        trsmn='120px',
        msrp='130px'
    )
)

gt.gtsave('table.png')
