import pandas as pd
from great_tables import GT, loc

df = pd.read_csv('./towny.csv')

# Calculate total growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct')[['name',
                                               'population_1996', 'population_2001', 'population_2006',
                                               'population_2011', 'population_2016', 'population_2021',
                                               'density_1996', 'density_2001', 'density_2006',
                                               'density_2011', 'density_2016', 'density_2021',
                                               'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                               'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                               'pop_change_2016_2021_pct', 'total_growth_pct']].reset_index(drop=True)

# Rename columns for better presentation
top_15.columns = ['Town',
                  'Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021',
                  'Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021',
                  '96→01 %', '01→06 %', '06→11 %', '11→16 %', '16→21 %', 'Total Growth %']

# Create the GT table
gt = (GT(top_15)
    .tab_header(
        title="Population Growth Trends: Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Density changes across census years (1996-2021) with percentage changes between periods"
    )
    .cols_label(
        **{col: col.replace('Dens', 'Density') for col in top_15.columns}
    )
    .fmt_number(
        columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021'],
        decimals=0
    )
    .fmt_number(
        columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021'],
        decimals=2
    )
    .fmt_percent(
        columns=['96→01 %', '01→06 %', '06→11 %', '11→16 %', '16→21 %', 'Total Growth %'],
        decimals=2
    )
    .tab_spanner(
        label="Population",
        columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021']
    )
    .tab_spanner(
        label="Density (persons/km²)",
        columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021']
    )
    .tab_spanner(
        label="Period Change %",
        columns=['96→01 %', '01→06 %', '06→11 %', '11→16 %', '16→21 %']
    )
    .data_color(
        columns=['96→01 %', '01→06 %', '06→11 %', '11→16 %', '16→21 %', 'Total Growth %'],
        domain=[-0.2, 0.6],
        palette=['#d73027', '#fee090', '#1a9850']
    )
    .cols_move_to_start(columns=['Town'])
)

gt.gtsave("table.png")
print("Table saved to table.png")
