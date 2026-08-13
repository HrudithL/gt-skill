import pandas as pd
from great_tables import GT, loc, md
from great_tables.data import exibble

# Load the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate 1996-2021
df['overall_growth'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth')[['name', 'density_1996', 'density_2001', 'density_2006',
                                              'density_2011', 'density_2016', 'density_2021',
                                              'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                              'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                              'pop_change_2016_2021_pct']].reset_index(drop=True)

# Round density values to 1 decimal and convert percentage changes to percentage format
top_15_display = top_15.copy()
for col in ['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']:
    top_15_display[col] = top_15_display[col].round(1)

for col in ['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
            'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']:
    top_15_display[col] = (top_15_display[col] * 100).round(1)

# Create the GT table
gt = (
    GT(top_15_display)
    .tab_header(
        title="Population Density Growth Trends: Ontario's Top 15 Fastest-Growing Towns (1996-2021)",
        subtitle="Population density (persons/km²) with period-over-period growth rates (%)"
    )
    .cols_label(
        name="Town",
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        pop_change_1996_2001_pct="'96-'01",
        pop_change_2001_2006_pct="'01-'06",
        pop_change_2006_2011_pct="'06-'11",
        pop_change_2011_2016_pct="'11-'16",
        pop_change_2016_2021_pct="'16-'21"
    )
    .tab_spanner(
        label="Density (persons/km²)",
        columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']
    )
    .tab_spanner(
        label="Population Change (%)",
        columns=['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']
    )
    .fmt_number(
        columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021'],
        decimals=1
    )
    .fmt_number(
        columns=['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct'],
        decimals=1,
        pattern="{x}%"
    )
    .cols_align(align="center", columns=['density_1996', 'density_2001', 'density_2006', 'density_2011',
                                          'density_2016', 'density_2021',
                                          'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                                          'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                                          'pop_change_2016_2021_pct'])
    .cols_align(align="left", columns=['name'])
    .tab_options(
        container_width="100%",
        table_width="100%"
    )
)

gt.gtsave("table.png")
