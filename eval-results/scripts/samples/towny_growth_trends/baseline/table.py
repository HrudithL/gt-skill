import pandas as pd
from great_tables import GT
from great_tables.style import fill
import polars as pl

# Read the data
df = pd.read_csv('towny.csv')

# Calculate average growth rate across all periods
growth_columns = ['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                  'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                  'pop_change_2016_2021_pct']

# Average growth rate
df['avg_growth_pct'] = df[growth_columns].mean(axis=1)

# Select rows where average growth is positive and remove NaN values
df_sorted = df.dropna(subset=['avg_growth_pct'])
df_sorted = df_sorted[df_sorted['avg_growth_pct'] > 0]

# Sort by average growth rate and get top 15
top_15 = df_sorted.nlargest(15, 'avg_growth_pct')[['name',
                                                     'density_1996', 'density_2001', 'density_2006',
                                                     'density_2011', 'density_2016', 'density_2021',
                                                     'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                                     'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                                     'pop_change_2016_2021_pct']].copy()

# Reset index to create row numbers
top_15 = top_15.reset_index(drop=True)
top_15.index = top_15.index + 1

# Rename columns for display
top_15.columns = ['Town', '1996', '2001', '2006', '2011', '2016', '2021',
                  'Change\n1996-2001', 'Change\n2001-2006', 'Change\n2006-2011',
                  'Change\n2011-2016', 'Change\n2016-2021']

# Format density values to 2 decimal places and growth rates as percentages
for col in ['1996', '2001', '2006', '2011', '2016', '2021']:
    top_15[col] = top_15[col].round(2)

for col in ['Change\n1996-2001', 'Change\n2001-2006', 'Change\n2006-2011', 'Change\n2011-2016', 'Change\n2016-2021']:
    top_15[col] = (top_15[col] * 100).round(1)

# Create GT table
gt = GT(top_15)

# Customize the table
gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle="Population Density Changes (persons/km²) and Growth Rates by Census Period (1996-2021)"
)

# Format density columns
gt = gt.fmt_number(
    columns=['1996', '2001', '2006', '2011', '2016', '2021'],
    decimals=2
)

# Format growth rate columns as percentages
gt = gt.fmt_number(
    columns=['Change\n1996-2001', 'Change\n2001-2006', 'Change\n2006-2011', 'Change\n2011-2016', 'Change\n2016-2021'],
    decimals=1,
    pattern="{x}%"
)

# Add spanners for density and growth columns
gt = gt.tab_spanner(
    label='Population Density (persons/km²)',
    columns=['1996', '2001', '2006', '2011', '2016', '2021']
)

gt = gt.tab_spanner(
    label='Population Growth Rate (%) Between Census Periods',
    columns=['Change\n1996-2001', 'Change\n2001-2006', 'Change\n2006-2011', 'Change\n2011-2016', 'Change\n2016-2021']
)

# Style the table
gt = gt.tab_options(
    table_font_size='12px',
    table_border_top_style='solid',
    table_border_bottom_style='solid'
)

# Save as PNG
gt.gtsave('table.png')
print("Table saved as table.png")
