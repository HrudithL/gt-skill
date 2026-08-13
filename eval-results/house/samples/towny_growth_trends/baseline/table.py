import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('./towny.csv')

# Calculate total growth from 1996 to 2021
df['total_growth_pct'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Filter out rows with missing data and sort by total growth
df_growth = df[df['population_1996'].notna() & df['population_2021'].notna()].copy()
df_growth = df_growth.sort_values('total_growth_pct', ascending=False)

# Get top 15 fastest-growing towns
top_15 = df_growth.head(15)

# Select columns for display
density_cols = ['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']
pct_cols = ['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
            'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']

# Create display data
display_data = top_15[['name'] + density_cols + pct_cols].copy()
display_data = display_data.sort_values('name').reset_index(drop=True)

# Round density values to 2 decimals
for col in density_cols:
    display_data[col] = display_data[col].round(2)

# Convert percentage changes to actual percentages (multiply by 100) and round to 1 decimal
for col in pct_cols:
    display_data[col] = (display_data[col] * 100).round(1)

# Rename columns for display
display_data.columns = ['Town',
                        'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021',
                        'Change 1996-2001 (%)', 'Change 2001-2006 (%)', 'Change 2006-2011 (%)',
                        'Change 2011-2016 (%)', 'Change 2016-2021 (%)']

# Create GT table
gt = (GT(display_data)
    .tab_header(
        title="Population Density Growth Trends",
        subtitle="Top 15 Fastest-Growing Ontario Towns (1996-2021)")
    .tab_spanner(
        label="Population Density (persons/km²)",
        columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'])
    .tab_spanner(
        label="Percentage Change Between Census Years",
        columns=['Change 1996-2001 (%)', 'Change 2001-2006 (%)', 'Change 2006-2011 (%)',
                'Change 2011-2016 (%)', 'Change 2016-2021 (%)'])
    .fmt_number(columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'],
                decimals=2)
    .fmt_number(columns=['Change 1996-2001 (%)', 'Change 2001-2006 (%)', 'Change 2006-2011 (%)',
                        'Change 2011-2016 (%)', 'Change 2016-2021 (%)'],
                decimals=1)
    .tab_options(
        container_width="100%",
        table_font_size="small"))

gt.gtsave("table.png")
