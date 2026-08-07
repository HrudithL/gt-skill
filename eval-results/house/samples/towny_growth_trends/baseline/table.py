import pandas as pd
from great_tables import GT
import numpy as np

# Read the data
df = pd.read_csv('towny.csv')

# Calculate total population growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct')[['name', 'population_1996', 'population_2001',
                                                'population_2006', 'population_2011',
                                                'population_2016', 'population_2021',
                                                'density_1996', 'density_2001', 'density_2006',
                                                'density_2011', 'density_2016', 'density_2021',
                                                'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                                'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                                'pop_change_2016_2021_pct', 'total_growth_pct']].copy()

# Calculate density changes between periods
top_15['density_change_1996_2001'] = ((top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996']) * 100
top_15['density_change_2001_2006'] = ((top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001']) * 100
top_15['density_change_2006_2011'] = ((top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006']) * 100
top_15['density_change_2011_2016'] = ((top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011']) * 100
top_15['density_change_2016_2021'] = ((top_15['density_2021'] - top_15['density_2016']) / top_15['density_2016']) * 100

# Create a clean dataframe for the table
table_data = pd.DataFrame({
    'Town': top_15['name'].values,
    '1996 Density': top_15['density_1996'].values,
    '1996-01 Change %': top_15['density_change_1996_2001'].values,
    '2001 Density': top_15['density_2001'].values,
    '2001-06 Change %': top_15['density_change_2001_2006'].values,
    '2006 Density': top_15['density_2006'].values,
    '2006-11 Change %': top_15['density_change_2006_2011'].values,
    '2011 Density': top_15['density_2011'].values,
    '2011-16 Change %': top_15['density_change_2011_2016'].values,
    '2016 Density': top_15['density_2016'].values,
    '2016-21 Change %': top_15['density_change_2016_2021'].values,
    '2021 Density': top_15['density_2021'].values,
    'Total Growth %': top_15['total_growth_pct'].values,
})

# Create GT table
gt = (
    GT(table_data)
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density (per km²) Across Census Years 1996-2021 with Period-to-Period Changes"
    )
    .fmt_number(
        columns=['1996 Density', '2001 Density', '2006 Density', '2011 Density', '2016 Density', '2021 Density'],
        decimals=2
    )
    .fmt_number(
        columns=['1996-01 Change %', '2001-06 Change %', '2006-11 Change %', '2011-16 Change %', '2016-21 Change %', 'Total Growth %'],
        decimals=1,
        pattern='{x}%'
    )
    .tab_options(
        table_width='100%',
        container_width='100%'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
