import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv('towny.csv')

# Calculate total population growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct').reset_index(drop=True)

# Helper function to calculate density percentage change
def density_pct_change(density_new, density_old):
    return (((density_new - density_old) / density_old) * 100).round(1)

# Create display dataframe
display_df = pd.DataFrame()
display_df['Town'] = top_15['name'].values

# 1996
display_df['Pop 1996'] = top_15['population_1996'].astype(int).values
display_df['Dens 1996'] = top_15['density_1996'].round(1).values

# 2001
display_df['Pop 2001'] = top_15['population_2001'].astype(int).values
display_df['Dens 2001'] = top_15['density_2001'].round(1).values
display_df['Pop% 96→01'] = (top_15['pop_change_1996_2001_pct'].values * 100).round(1)
display_df['Dens% 96→01'] = density_pct_change(top_15['density_2001'], top_15['density_1996']).values

# 2006
display_df['Pop 2006'] = top_15['population_2006'].astype(int).values
display_df['Dens 2006'] = top_15['density_2006'].round(1).values
display_df['Pop% 01→06'] = (top_15['pop_change_2001_2006_pct'].values * 100).round(1)
display_df['Dens% 01→06'] = density_pct_change(top_15['density_2006'], top_15['density_2001']).values

# 2011
display_df['Pop 2011'] = top_15['population_2011'].astype(int).values
display_df['Dens 2011'] = top_15['density_2011'].round(1).values
display_df['Pop% 06→11'] = (top_15['pop_change_2006_2011_pct'].values * 100).round(1)
display_df['Dens% 06→11'] = density_pct_change(top_15['density_2011'], top_15['density_2006']).values

# 2016
display_df['Pop 2016'] = top_15['population_2016'].astype(int).values
display_df['Dens 2016'] = top_15['density_2016'].round(1).values
display_df['Pop% 11→16'] = (top_15['pop_change_2011_2016_pct'].values * 100).round(1)
display_df['Dens% 11→16'] = density_pct_change(top_15['density_2016'], top_15['density_2011']).values

# 2021
display_df['Pop 2021'] = top_15['population_2021'].astype(int).values
display_df['Dens 2021'] = top_15['density_2021'].round(1).values
display_df['Pop% 16→21'] = (top_15['pop_change_2016_2021_pct'].values * 100).round(1)
display_df['Dens% 16→21'] = density_pct_change(top_15['density_2021'], top_15['density_2016']).values

# Total growth
display_df['Total% 96→21'] = top_15['total_growth_pct'].round(1).values

# Create GT table
gt = (
    GT(display_df)
    .tab_header(
        title="Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Population and Density Trends with 5-Year Period Changes (1996-2021)"
    )
    .tab_spanner(
        label='1996',
        columns=['Pop 1996', 'Dens 1996']
    )
    .tab_spanner(
        label='2001',
        columns=['Pop 2001', 'Dens 2001', 'Pop% 96→01', 'Dens% 96→01']
    )
    .tab_spanner(
        label='2006',
        columns=['Pop 2006', 'Dens 2006', 'Pop% 01→06', 'Dens% 01→06']
    )
    .tab_spanner(
        label='2011',
        columns=['Pop 2011', 'Dens 2011', 'Pop% 06→11', 'Dens% 06→11']
    )
    .tab_spanner(
        label='2016',
        columns=['Pop 2016', 'Dens 2016', 'Pop% 11→16', 'Dens% 11→16']
    )
    .tab_spanner(
        label='2021',
        columns=['Pop 2021', 'Dens 2021', 'Pop% 16→21']
    )
    .fmt_integer(
        columns=[col for col in display_df.columns if col.startswith('Pop')]
    )
    .fmt_number(
        columns=[col for col in display_df.columns if col.startswith('Dens') and '→' not in col],
        decimals=1
    )
    .fmt_number(
        columns=[col for col in display_df.columns if '→' in col or 'Total' in col],
        decimals=1
    )
    .tab_source_note(
        "Data source: towny.csv. Dens = Population Density (persons/km²). % changes calculated between adjacent census periods. Top 15 towns ranked by total population growth 1996-2021."
    )
)

gt.gtsave('table.png')
print("Table successfully generated and saved to table.png")
