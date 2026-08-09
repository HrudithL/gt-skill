import pandas as pd
from great_tables import GT
import numpy as np

df = pd.read_csv('towny.csv')

# Calculate overall population growth from 1996 to 2021
df['overall_growth'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Filter out rows with missing 1996 data
df_clean = df[df['population_1996'].notna()].copy()

# Get top 15 fastest-growing towns (by overall growth percentage)
top_15 = df_clean.nlargest(15, 'overall_growth')[['name', 'population_1996', 'population_2001',
                                                    'population_2006', 'population_2011', 'population_2016',
                                                    'population_2021', 'density_1996', 'density_2001',
                                                    'density_2006', 'density_2011', 'density_2016', 'density_2021',
                                                    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                                    'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                                    'pop_change_2016_2021_pct']].copy()

# Prepare data for table
table_data = []
for _, row in top_15.iterrows():
    table_data.append({
        'Town': row['name'],
        'Pop 1996': f"{int(row['population_1996']):,}",
        'Dens 1996': f"{row['density_1996']:.2f}",
        'Δ% 96-01': f"{row['pop_change_1996_2001_pct']*100:.1f}%",
        'Pop 2001': f"{int(row['population_2001']):,}",
        'Dens 2001': f"{row['density_2001']:.2f}",
        'Δ% 01-06': f"{row['pop_change_2001_2006_pct']*100:.1f}%",
        'Pop 2006': f"{int(row['population_2006']):,}",
        'Dens 2006': f"{row['density_2006']:.2f}",
        'Δ% 06-11': f"{row['pop_change_2006_2011_pct']*100:.1f}%",
        'Pop 2011': f"{int(row['population_2011']):,}",
        'Dens 2011': f"{row['density_2011']:.2f}",
        'Δ% 11-16': f"{row['pop_change_2011_2016_pct']*100:.1f}%",
        'Pop 2016': f"{int(row['population_2016']):,}",
        'Dens 2016': f"{row['density_2016']:.2f}",
        'Δ% 16-21': f"{row['pop_change_2016_2021_pct']*100:.1f}%",
        'Pop 2021': f"{int(row['population_2021']):,}",
        'Dens 2021': f"{row['density_2021']:.2f}",
    })

table_df = pd.DataFrame(table_data)

# Create GT table
gt = (
    GT(table_df)
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population and Density Changes Across Census Years (1996-2021)"
    )
    .tab_spanner(
        label="1996-2001 Period",
        columns=['Pop 1996', 'Dens 1996', 'Δ% 96-01', 'Pop 2001', 'Dens 2001']
    )
    .tab_spanner(
        label="2001-2006 Period",
        columns=['Δ% 01-06', 'Pop 2006', 'Dens 2006']
    )
    .tab_spanner(
        label="2006-2011 Period",
        columns=['Δ% 06-11', 'Pop 2011', 'Dens 2011']
    )
    .tab_spanner(
        label="2011-2016 Period",
        columns=['Δ% 11-16', 'Pop 2016', 'Dens 2016']
    )
    .tab_spanner(
        label="2016-2021 Period",
        columns=['Δ% 16-21', 'Pop 2021', 'Dens 2021']
    )
    .cols_label(
        Town="Town Name"
    )
    .tab_source_note("Source: Census data from Statistics Canada (1996-2021). Density measured in persons per km². Population percentage changes shown for each 5-year period.")
    .opt_row_striping()
)

gt.gtsave("table.png")
