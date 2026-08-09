import pandas as pd
from great_tables import GT

df = pd.read_csv('towny.csv')

# Calculate overall growth rate (1996-2021)
df['overall_growth'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth')[['name', 'population_1996', 'population_2001', 'population_2006',
                                             'population_2011', 'population_2016', 'population_2021',
                                             'density_1996', 'density_2001', 'density_2006',
                                             'density_2011', 'density_2016', 'density_2021',
                                             'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                             'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                             'pop_change_2016_2021_pct']].reset_index(drop=True)

# Create display dataframe with formatted values
display_df = pd.DataFrame()
display_df['Town'] = top_15['name']

# Population columns
display_df['Pop 1996'] = top_15['population_1996'].astype(int)
display_df['Pop 2001'] = top_15['population_2001'].astype(int)
display_df['Pop 2006'] = top_15['population_2006'].astype(int)
display_df['Pop 2011'] = top_15['population_2011'].astype(int)
display_df['Pop 2016'] = top_15['population_2016'].astype(int)
display_df['Pop 2021'] = top_15['population_2021'].astype(int)

# Density columns (persons/km²)
display_df['Den 1996'] = top_15['density_1996'].round(2)
display_df['Den 2001'] = top_15['density_2001'].round(2)
display_df['Den 2006'] = top_15['density_2006'].round(2)
display_df['Den 2011'] = top_15['density_2011'].round(2)
display_df['Den 2016'] = top_15['density_2016'].round(2)
display_df['Den 2021'] = top_15['density_2021'].round(2)

# Growth percentage columns
display_df['Δ% 96-01'] = (top_15['pop_change_1996_2001_pct'] * 100).round(1)
display_df['Δ% 01-06'] = (top_15['pop_change_2001_2006_pct'] * 100).round(1)
display_df['Δ% 06-11'] = (top_15['pop_change_2006_2011_pct'] * 100).round(1)
display_df['Δ% 11-16'] = (top_15['pop_change_2011_2016_pct'] * 100).round(1)
display_df['Δ% 16-21'] = (top_15['pop_change_2016_2021_pct'] * 100).round(1)

# Create GT table
gt_table = (
    GT(display_df)
    .tab_header(
        title="Ontario's Top 15 Fastest-Growing Towns (1996–2021)",
        subtitle="Population, density, and growth rates across all census periods"
    )
    .tab_spanner(
        label="Population",
        columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021']
    )
    .tab_spanner(
        label="Density (persons/km²)",
        columns=['Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021']
    )
    .tab_spanner(
        label="Period Growth (%)",
        columns=['Δ% 96-01', 'Δ% 01-06', 'Δ% 06-11', 'Δ% 11-16', 'Δ% 16-21']
    )
    .fmt_number(columns=['Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021'], decimals=2)
    .fmt_number(columns=['Δ% 96-01', 'Δ% 01-06', 'Δ% 06-11', 'Δ% 11-16', 'Δ% 16-21'], decimals=1)
    .cols_align(align='center', columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021',
                                          'Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021',
                                          'Δ% 96-01', 'Δ% 01-06', 'Δ% 06-11', 'Δ% 11-16', 'Δ% 16-21'])
    .cols_align(align='left', columns=['Town'])
)

gt_table.gtsave("table.png")
