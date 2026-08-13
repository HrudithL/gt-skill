import pandas as pd
import polars as pl
from great_tables import GT, loc, style
import math

df = pd.read_csv('towny.csv')

# Calculate overall growth rate (1996 to 2021)
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Sort by overall growth and get top 15
top_15 = df.nlargest(15, 'overall_growth_pct')

# Build the display table with density values and percentage changes
data = []
for _, row in top_15.iterrows():
    town = row['name']

    # Densities across all census years
    density_1996 = row['density_1996']
    density_2001 = row['density_2001']
    density_2006 = row['density_2006']
    density_2011 = row['density_2011']
    density_2016 = row['density_2016']
    density_2021 = row['density_2021']

    # Calculate percentage changes in density between periods
    change_1996_2001 = ((density_2001 - density_1996) / density_1996) * 100 if density_1996 > 0 else 0
    change_2001_2006 = ((density_2006 - density_2001) / density_2001) * 100 if density_2001 > 0 else 0
    change_2006_2011 = ((density_2011 - density_2006) / density_2006) * 100 if density_2006 > 0 else 0
    change_2011_2016 = ((density_2016 - density_2011) / density_2011) * 100 if density_2011 > 0 else 0
    change_2016_2021 = ((density_2021 - density_2016) / density_2016) * 100 if density_2016 > 0 else 0

    data.append({
        'Town': town,
        'Density 1996': density_1996,
        'Density 2001': density_2001,
        '% Change 96-01': change_1996_2001,
        'Density 2006': density_2006,
        '% Change 01-06': change_2001_2006,
        'Density 2011': density_2011,
        '% Change 06-11': change_2006_2011,
        'Density 2016': density_2016,
        '% Change 11-16': change_2011_2016,
        'Density 2021': density_2021,
        '% Change 16-21': change_2016_2021,
    })

result_df = pd.DataFrame(data)

# Create GT table
gt = (
    GT(result_df)
    .tab_header(
        title="Ontario Towns: Population Density Growth Trends",
        subtitle="Top 15 Fastest-Growing Towns (1996-2021) with Density Changes Across Census Years"
    )
    .fmt_number(columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'], decimals=1)
    .fmt_number(columns=['% Change 96-01', '% Change 01-06', '% Change 06-11', '% Change 11-16', '% Change 16-21'], decimals=1)
    .tab_spanner(label="1996 Census", columns=['Density 1996'])
    .tab_spanner(label="2001 Census", columns=['Density 2001', '% Change 96-01'])
    .tab_spanner(label="2006 Census", columns=['Density 2006', '% Change 01-06'])
    .tab_spanner(label="2011 Census", columns=['Density 2011', '% Change 06-11'])
    .tab_spanner(label="2016 Census", columns=['Density 2016', '% Change 11-16'])
    .tab_spanner(label="2021 Census", columns=['Density 2021', '% Change 16-21'])
    .opt_vertical_padding(scale=0.6)
)

gt.gtsave('table.png')
print("Table saved to table.png")
