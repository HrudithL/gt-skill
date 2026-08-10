import pandas as pd
import polars as pl
from great_tables import GT

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall growth (1996 to 2021)
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100).round(2)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')

# Create a table with town name and density changes across census years
data = []
for _, row in top_15.iterrows():
    density_cols = ['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']
    densities = [row[col] for col in density_cols]

    pct_change_cols = ['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                       'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']
    pct_changes = [row[col] * 100 for col in pct_change_cols]

    data.append({
        'Town': row['name'],
        'Density 1996': densities[0],
        'Density 2001': densities[1],
        'Change 1996-2001 (%)': pct_changes[0],
        'Density 2006': densities[2],
        'Change 2001-2006 (%)': pct_changes[1],
        'Density 2011': densities[3],
        'Change 2006-2011 (%)': pct_changes[2],
        'Density 2016': densities[4],
        'Change 2011-2016 (%)': pct_changes[3],
        'Density 2021': densities[5],
        'Change 2016-2021 (%)': pct_changes[4],
        'Overall Growth (%)': row['overall_growth_pct']
    })

table_df = pd.DataFrame(data)

# Create the great_tables GT object
gt = (GT(table_df)
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density (people/km²) and Percentage Changes Across Census Years (1996-2021)"
    )
    .cols_label(
        Town="Town",
        **{
            'Density 1996': '1996',
            'Density 2001': '2001',
            'Change 1996-2001 (%)': 'Change %',
            'Density 2006': '2006',
            'Change 2001-2006 (%)': 'Change %',
            'Density 2011': '2011',
            'Change 2006-2011 (%)': 'Change %',
            'Density 2016': '2016',
            'Change 2011-2016 (%)': 'Change %',
            'Density 2021': '2021',
            'Change 2016-2021 (%)': 'Change %',
            'Overall Growth (%)': 'Overall Growth %'
        }
    )
    .tab_spanner(label="1996-2001", columns=['Density 1996', 'Density 2001', 'Change 1996-2001 (%)'])
    .tab_spanner(label="2001-2006", columns=['Density 2006', 'Change 2001-2006 (%)'])
    .tab_spanner(label="2006-2011", columns=['Density 2011', 'Change 2006-2011 (%)'])
    .tab_spanner(label="2011-2016", columns=['Density 2016', 'Change 2011-2016 (%)'])
    .tab_spanner(label="2016-2021", columns=['Density 2021', 'Change 2016-2021 (%)'])
    .fmt_number(columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'], decimals=1)
    .fmt_number(columns=['Change 1996-2001 (%)', 'Change 2001-2006 (%)', 'Change 2006-2011 (%)',
                         'Change 2011-2016 (%)', 'Change 2016-2021 (%)', 'Overall Growth (%)'], decimals=2)
    .opt_align_table_header(align='center')
    .tab_options(
        table_font_size='small',
        table_border_top_style='solid',
        table_border_bottom_style='solid'
    )
)

gt.gtsave('table.png')
