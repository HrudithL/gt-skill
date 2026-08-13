import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Filter to only towns with positive growth (to avoid division issues)
df_growth = df[df['overall_growth_pct'] > 0].copy()

# Sort by overall growth percentage and get top 15
top_15 = df_growth.nlargest(15, 'overall_growth_pct')[['name', 'density_1996', 'density_2001', 'density_2006',
                                                         'density_2011', 'density_2016', 'density_2021',
                                                         'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                                         'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                                         'pop_change_2016_2021_pct', 'overall_growth_pct']].copy()

# Calculate density percentage changes between census periods
top_15['density_change_1996_2001_pct'] = ((top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996']) * 100
top_15['density_change_2001_2006_pct'] = ((top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001']) * 100
top_15['density_change_2006_2011_pct'] = ((top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006']) * 100
top_15['density_change_2011_2016_pct'] = ((top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011']) * 100
top_15['density_change_2016_2021_pct'] = ((top_15['density_2021'] - top_15['density_2016']) / top_15['density_2016']) * 100

# Reorder columns for better presentation
display_df = top_15[[
    'name',
    'density_1996', 'density_change_1996_2001_pct',
    'density_2001', 'density_change_2001_2006_pct',
    'density_2006', 'density_change_2006_2011_pct',
    'density_2011', 'density_change_2011_2016_pct',
    'density_2016', 'density_change_2016_2021_pct',
    'density_2021', 'overall_growth_pct'
]].copy()

# Reset index for cleaner table
display_df = display_df.reset_index(drop=True)

# Create the table
gt = GT(display_df)

# Format numbers
gt = gt.fmt_number(columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021'],
                   decimals=1)
gt = gt.fmt_percent(columns=['density_change_1996_2001_pct', 'density_change_2001_2006_pct',
                             'density_change_2006_2011_pct', 'density_change_2011_2016_pct',
                             'density_change_2016_2021_pct', 'overall_growth_pct'],
                    decimals=1)

# Add column labels
gt = gt.cols_label(
    name='Town',
    density_1996='Density 1996',
    density_change_1996_2001_pct='% Change\n1996-2001',
    density_2001='Density 2001',
    density_change_2001_2006_pct='% Change\n2001-2006',
    density_2006='Density 2006',
    density_change_2006_2011_pct='% Change\n2006-2011',
    density_2011='Density 2011',
    density_change_2011_2016_pct='% Change\n2011-2016',
    density_2016='Density 2016',
    density_change_2016_2021_pct='% Change\n2016-2021',
    density_2021='Density 2021',
    overall_growth_pct='Overall\nGrowth %'
)

# Set title
gt = gt.tab_header(
    title='Population Growth Trends: Top 15 Fastest-Growing Ontario Towns',
    subtitle='Density Changes Across Census Years (1996-2021) with Period-over-Period Percentage Changes'
)

gt.gtsave('table.png')
print("Table saved to table.png")
