import pandas as pd
from great_tables import GT

# Load the CSV file
df = pd.read_csv('gtcars.csv')

# Select relevant columns and get top 5 by horsepower
top_5 = df[['mfr', 'model', 'year', 'hp', 'msrp']].nlargest(5, 'hp')

# Reset index for cleaner display
top_5 = top_5.reset_index(drop=True)

# Rename columns for better display
top_5 = top_5.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'year': 'Year',
    'hp': 'Horsepower',
    'msrp': 'MSRP'
})

# Create the table with great_tables
gt = (
    GT(top_5)
    .tab_header(
        title="Top 5 Cars by Horsepower",
        subtitle="Comparison of the most powerful vehicles in the dataset"
    )
    .fmt_integer(columns=['Year', 'Horsepower'])
    .fmt_currency(columns=['MSRP'], currency='USD')
)

# Save as PNG
gt.gtsave('table.png')
print("Table saved successfully as table.png")
print("\nTop 5 Cars by Horsepower:")
print(top_5.to_string(index=False))
