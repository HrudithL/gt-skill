import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')

# Sort by country, then by price descending
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Select and rename columns for display
display_df = top_10[['mfr', 'model', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Country', 'MSRP', 'Drivetrain', 'Transmission']

# Create the GT table with grouping by country
gt_table = (
    GT(display_df, rowname_col='Country')
    .tab_header(
        title='Top 10 Most Expensive GT Cars by Country',
        subtitle='Includes drivetrain and transmission details'
    )
    .fmt_currency(columns='MSRP', currency='USD')
)

# Save the table
gt_table.gtsave('table.png')
print("Table saved to table.png")
