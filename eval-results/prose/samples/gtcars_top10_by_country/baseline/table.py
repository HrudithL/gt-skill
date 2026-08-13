import pandas as pd
from great_tables import GT
from great_tables.data import gtcars

# Read the gtcars.csv file
df = pd.read_csv('gtcars.csv')

# Sort by MSRP descending and take top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')

# Sort by country, then by MSRP descending for better grouping
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Select and rename columns for display
display_df = top_10_sorted[['mfr', 'model', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Country', 'Drivetrain', 'Transmission', 'MSRP']

# Format the table
gt_table = (
    GT(display_df)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .fmt_currency(columns=['MSRP'], currency='USD')
    .cols_align(align='center', columns=['Drivetrain', 'Transmission'])
    .cols_align(align='left', columns=['Manufacturer', 'Model', 'Country'])
    .cols_align(align='right', columns=['MSRP'])
    .tab_options(
        container_width='100%'
    )
)

gt_table.gtsave('table.png')
