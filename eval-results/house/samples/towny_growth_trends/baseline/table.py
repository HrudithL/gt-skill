import pandas as pd
from great_tables import GT
import great_tables as gt

# Load the data
df = pd.read_csv('towny.csv')

# Calculate total growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct')[['name', 'population_1996', 'population_2001', 'population_2006',
                                                 'population_2011', 'population_2016', 'population_2021',
                                                 'density_1996', 'density_2001', 'density_2006',
                                                 'density_2011', 'density_2016', 'density_2021']].reset_index(drop=True)

# Create a result table with density and percentage changes
def safe_pct_change(new_val, old_val):
    if old_val == 0:
        return None
    return round(((new_val - old_val) / old_val * 100), 1)

result_rows = []
for idx, row in top_15.iterrows():
    result_rows.append({
        'Town': row['name'],
        'Pop 1996': int(row['population_1996']),
        'Dens 1996': round(row['density_1996'], 2),
        'Dens 2001': round(row['density_2001'], 2),
        '% Δ 96-01': safe_pct_change(row['density_2001'], row['density_1996']),
        'Dens 2006': round(row['density_2006'], 2),
        '% Δ 01-06': safe_pct_change(row['density_2006'], row['density_2001']),
        'Dens 2011': round(row['density_2011'], 2),
        '% Δ 06-11': safe_pct_change(row['density_2011'], row['density_2006']),
        'Dens 2016': round(row['density_2016'], 2),
        '% Δ 11-16': safe_pct_change(row['density_2016'], row['density_2011']),
        'Dens 2021': round(row['density_2021'], 2),
        '% Δ 16-21': safe_pct_change(row['density_2021'], row['density_2016']),
    })

result_df = pd.DataFrame(result_rows)

# Create the GT table
gt_table = (
    GT(result_df)
    .tab_header(
        title="Population Density Growth Trends",
        subtitle="Top 15 Fastest-Growing Ontario Towns (1996-2021)"
    )
    .tab_spanner(
        label="1996-2001",
        columns=['Dens 2001', '% Δ 96-01']
    )
    .tab_spanner(
        label="2001-2006",
        columns=['Dens 2006', '% Δ 01-06']
    )
    .tab_spanner(
        label="2006-2011",
        columns=['Dens 2011', '% Δ 06-11']
    )
    .tab_spanner(
        label="2011-2016",
        columns=['Dens 2016', '% Δ 11-16']
    )
    .tab_spanner(
        label="2016-2021",
        columns=['Dens 2021', '% Δ 16-21']
    )
    .fmt_number(
        columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021'],
        decimals=1
    )
    .fmt_number(
        columns=['Pop 1996'],
        sep_mark=',',
        decimals=0
    )
    .tab_options(
        container_overflow_x="visible"
    )
)

gt_table.gtsave("table.png")
