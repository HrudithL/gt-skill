import pandas as pd
import great_tables as gt

# Load the data
df = pd.read_csv('towny.csv')

# Calculate total growth from 1996 to 2021
df['total_growth_pct'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Sort by total growth and get top 15
top_15 = df.nlargest(15, 'total_growth_pct')[['name', 'population_1996', 'population_2021',
    'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
    'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct', 'total_growth_pct']].reset_index(drop=True)

# Build the GT table
gt_table = (
    gt.GT(top_15)
    .tab_header(
        title="Ontario's Fastest-Growing Towns (1996-2021)",
        subtitle="Population Growth Trends and Density Changes Across Census Years"
    )
    .fmt_number(
        columns=['population_1996', 'population_2021'],
        decimals=0
    )
    .fmt_number(
        columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021'],
        decimals=2
    )
    .fmt_percent(
        columns=['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct', 'total_growth_pct'],
        decimals=1
    )
    .cols_label(
        name="Town",
        population_1996="1996 Pop",
        population_2021="2021 Pop",
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        pop_change_1996_2001_pct="1996-2001",
        pop_change_2001_2006_pct="2001-2006",
        pop_change_2006_2011_pct="2006-2011",
        pop_change_2011_2016_pct="2011-2016",
        pop_change_2016_2021_pct="2016-2021",
        total_growth_pct="1996-2021"
    )
    .tab_spanner(
        label="Population",
        columns=['population_1996', 'population_2021']
    )
    .tab_spanner(
        label="Population Density (persons/km²)",
        columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']
    )
    .tab_spanner(
        label="Population Growth %",
        columns=['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct', 'total_growth_pct']
    )
    .data_color(
        columns=['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct', 'total_growth_pct'],
        palette="RdYlGn",
        domain=[-0.1, 0.5]
    )
    .tab_source_note(
        "Source: Statistics Canada Census Data (1996-2021)"
    )
    .opt_row_striping()
)

gt_table.gtsave("table.png")
