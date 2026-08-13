import pandas as pd
from great_tables import GT, style, loc

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']]
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Rename columns for display
top_10.columns = ['Manufacturer', 'Model', 'Country', 'MSRP', 'Drivetrain', 'Transmission']

# Create GT table
gt = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .fmt_currency(columns='MSRP', currency='USD')
    .cols_label(
        Manufacturer='Manufacturer',
        Model='Model',
        Country='Country',
        MSRP='MSRP',
        Drivetrain='Drivetrain',
        Transmission='Transmission'
    )
)

gt.gtsave('table.png')
