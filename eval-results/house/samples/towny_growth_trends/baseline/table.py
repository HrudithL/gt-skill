import pandas as pd
from great_tables import GT

df = pd.read_csv('towny.csv')

# Calculate overall population growth from 1996 to 2021
df['overall_growth'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100).round(2)

# Filter to get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth')

# Build the output dataframe with density and percentage changes
output_data = []
for _, row in top_15.iterrows():
    # Density values for each census year
    density_1996 = row['density_1996']
    density_2001 = row['density_2001']
    density_2006 = row['density_2006']
    density_2011 = row['density_2011']
    density_2016 = row['density_2016']
    density_2021 = row['density_2021']

    # Calculate percentage changes between census periods
    pct_1996_2001 = ((density_2001 - density_1996) / density_1996 * 100) if density_1996 > 0 else 0
    pct_2001_2006 = ((density_2006 - density_2001) / density_2001 * 100) if density_2001 > 0 else 0
    pct_2006_2011 = ((density_2011 - density_2006) / density_2006 * 100) if density_2006 > 0 else 0
    pct_2011_2016 = ((density_2016 - density_2011) / density_2011 * 100) if density_2011 > 0 else 0
    pct_2016_2021 = ((density_2021 - density_2016) / density_2016 * 100) if density_2016 > 0 else 0

    output_data.append({
        'Town': row['name'],
        'Density 1996': density_1996,
        'Chg 96-01 (%)': pct_1996_2001,
        'Density 2001': density_2001,
        'Chg 01-06 (%)': pct_2001_2006,
        'Density 2006': density_2006,
        'Chg 06-11 (%)': pct_2006_2011,
        'Density 2011': density_2011,
        'Chg 11-16 (%)': pct_2011_2016,
        'Density 2016': density_2016,
        'Chg 16-21 (%)': pct_2016_2021,
        'Density 2021': density_2021,
        'Overall Growth (%)': row['overall_growth']
    })

output_df = pd.DataFrame(output_data)

# Create the table
gt = (
    GT(output_df)
    .fmt_number(
        columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'],
        decimals=2
    )
    .fmt_number(
        columns=['Chg 96-01 (%)', 'Chg 01-06 (%)', 'Chg 06-11 (%)', 'Chg 11-16 (%)', 'Chg 16-21 (%)', 'Overall Growth (%)'],
        decimals=1
    )
    .tab_header(
        title='Population Density Trends for Top 15 Fastest-Growing Ontario Towns (1996-2021)',
        subtitle='Density values (persons/km²) with percentage changes between census periods'
    )
)

gt.gtsave('table.png')
print('Table saved to table.png')
