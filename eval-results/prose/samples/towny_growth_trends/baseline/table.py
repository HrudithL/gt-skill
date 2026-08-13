import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Sort by overall growth and get top 15
top_15 = df.nlargest(15, 'overall_growth')[['name', 'population_1996', 'population_2021',
                                              'density_1996', 'density_2001', 'density_2006',
                                              'density_2011', 'density_2016', 'density_2021',
                                              'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                              'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                              'pop_change_2016_2021_pct', 'overall_growth']].copy()

# Calculate density change percentages between periods
top_15['density_change_1996_2001_pct'] = ((top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996']) * 100
top_15['density_change_2001_2006_pct'] = ((top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001']) * 100
top_15['density_change_2006_2011_pct'] = ((top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006']) * 100
top_15['density_change_2011_2016_pct'] = ((top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011']) * 100
top_15['density_change_2016_2021_pct'] = ((top_15['density_2021'] - top_15['density_2016']) / top_15['density_2016']) * 100

# Create the display table with selected columns
display_df = pd.DataFrame({
    'Town': top_15['name'].values,
    'Pop 1996': top_15['population_1996'].astype(int).values,
    'Pop 2021': top_15['population_2021'].astype(int).values,
    'Overall Growth %': top_15['overall_growth'].round(1).values,
    'Dens 1996': top_15['density_1996'].round(2).values,
    'Dens 2001': top_15['density_2001'].round(2).values,
    'Δ% 96-01': top_15['density_change_1996_2001_pct'].round(1).values,
    'Dens 2006': top_15['density_2006'].round(2).values,
    'Δ% 01-06': top_15['density_change_2001_2006_pct'].round(1).values,
    'Dens 2011': top_15['density_2011'].round(2).values,
    'Δ% 06-11': top_15['density_change_2006_2011_pct'].round(1).values,
    'Dens 2016': top_15['density_2016'].round(2).values,
    'Δ% 11-16': top_15['density_change_2011_2016_pct'].round(1).values,
    'Dens 2021': top_15['density_2021'].round(2).values,
    'Δ% 16-21': top_15['density_change_2016_2021_pct'].round(1).values,
})

# Create GT object
gt = (GT(display_df)
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns (1996-2021)",
        subtitle="Density (persons/km²) and Percentage Changes Across Census Years"
    )
    .fmt_number(
        columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021'],
        decimals=1
    )
    .fmt_number(
        columns=['Pop 1996', 'Pop 2021'],
        decimals=0
    )
    .fmt_number(
        columns=['Overall Growth %',
                 'Δ% 96-01', 'Δ% 01-06',
                 'Δ% 06-11', 'Δ% 11-16', 'Δ% 16-21'],
        decimals=1
    )
    .tab_spanner(
        label="Population",
        columns=['Pop 1996', 'Pop 2021', 'Overall Growth %']
    )
    .tab_spanner(
        label="1996-2001",
        columns=['Dens 1996', 'Dens 2001', 'Δ% 96-01']
    )
    .tab_spanner(
        label="2001-2006",
        columns=['Dens 2006', 'Δ% 01-06']
    )
    .tab_spanner(
        label="2006-2011",
        columns=['Dens 2011', 'Δ% 06-11']
    )
    .tab_spanner(
        label="2011-2016",
        columns=['Dens 2016', 'Δ% 11-16']
    )
    .tab_spanner(
        label="2016-2021",
        columns=['Dens 2021', 'Δ% 16-21']
    )
)

gt.gtsave('table.png')
