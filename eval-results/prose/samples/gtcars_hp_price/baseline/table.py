import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('gtcars.csv')

# Select and rename columns for display
display_df = df[['mfr', 'model', 'hp', 'msrp']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Horsepower', 'Price']

# Format price as currency
display_df['Price'] = display_df['Price'].apply(lambda x: f'${x:,.0f}')

# Create the table
gt_table = (
    GT(display_df)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications for high-end vehicles"
    )
    .opt_align_table_header("left")
)

# Render to PNG
gt_table.gtsave("table.png")
print("Table saved to table.png")
