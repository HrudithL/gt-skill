import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')[['name', 'population_1996', 'population_2001', 'population_2006',
                                                   'population_2011', 'population_2016', 'population_2021',
                                                   'density_1996', 'density_2001', 'density_2006',
                                                   'density_2011', 'density_2016', 'density_2021',
                                                   'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                                   'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                                   'pop_change_2016_2021_pct']].reset_index(drop=True)

# Create a formatted table with population and density data
table_data = []
for idx, row in top_15.iterrows():
    table_data.append({
        'Town': row['name'],
        'Pop 1996': int(row['population_1996']),
        'Pop 2001': int(row['population_2001']),
        'Δ 1996-2001 %': f"{row['pop_change_1996_2001_pct']*100:.1f}%",
        'Pop 2006': int(row['population_2006']),
        'Δ 2001-2006 %': f"{row['pop_change_2001_2006_pct']*100:.1f}%",
        'Pop 2011': int(row['population_2011']),
        'Δ 2006-2011 %': f"{row['pop_change_2006_2011_pct']*100:.1f}%",
        'Pop 2016': int(row['population_2016']),
        'Δ 2011-2016 %': f"{row['pop_change_2011_2016_pct']*100:.1f}%",
        'Pop 2021': int(row['population_2021']),
        'Δ 2016-2021 %': f"{row['pop_change_2016_2021_pct']*100:.1f}%",
        'Dens 1996': f"{row['density_1996']:.1f}",
        'Dens 2001': f"{row['density_2001']:.1f}",
        'Dens 2006': f"{row['density_2006']:.1f}",
        'Dens 2011': f"{row['density_2011']:.1f}",
        'Dens 2016': f"{row['density_2016']:.1f}",
        'Dens 2021': f"{row['density_2021']:.1f}",
    })

table_df = pd.DataFrame(table_data)

# Create Great Tables visualization
gt_table = (
    GT(table_df)
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population & Density Changes Across Census Years (1996-2021)"
    )
    .tab_spanner(
        label="Population",
        columns=['Pop 1996', 'Pop 2001', 'Δ 1996-2001 %', 'Pop 2006', 'Δ 2001-2006 %',
                 'Pop 2011', 'Δ 2006-2011 %', 'Pop 2016', 'Δ 2011-2016 %', 'Pop 2021', 'Δ 2016-2021 %']
    )
    .tab_spanner(
        label="Population Density (per km²)",
        columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021']
    )
    .cols_align(align="center")
    .cols_align(align="left", columns=['Town'])
)

gt_table.gtsave("table.png")
print("Table saved to table.png")
