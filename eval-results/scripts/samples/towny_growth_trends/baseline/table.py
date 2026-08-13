import pandas as pd
import polars as pl
from great_tables import GT, style, loc
import re

df = pd.read_csv('towny.csv')

# Calculate overall population growth from 1996 to 2021
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')[['name', 'population_1996', 'density_1996',
                                                  'population_2001', 'density_2001',
                                                  'population_2006', 'density_2006',
                                                  'population_2011', 'density_2011',
                                                  'population_2016', 'density_2016',
                                                  'population_2021', 'density_2021',
                                                  'pop_change_1996_2001_pct',
                                                  'pop_change_2001_2006_pct',
                                                  'pop_change_2006_2011_pct',
                                                  'pop_change_2011_2016_pct',
                                                  'pop_change_2016_2021_pct',
                                                  'overall_growth_pct']].copy()

# Reset index for cleaner output
top_15 = top_15.reset_index(drop=True)

# Create a display table with formatted columns
display_data = []
for idx, row in top_15.iterrows():
    display_data.append({
        'Town': row['name'],
        '1996 Pop': f"{int(row['population_1996']):,}",
        '1996 Den': f"{row['density_1996']:.1f}",
        '2001 Pop': f"{int(row['population_2001']):,}",
        '2001 Den': f"{row['density_2001']:.1f}",
        '96→01 Δ%': f"{row['pop_change_1996_2001_pct']*100:.1f}%",
        '2006 Pop': f"{int(row['population_2006']):,}",
        '2006 Den': f"{row['density_2006']:.1f}",
        '01→06 Δ%': f"{row['pop_change_2001_2006_pct']*100:.1f}%",
        '2011 Pop': f"{int(row['population_2011']):,}",
        '2011 Den': f"{row['density_2011']:.1f}",
        '06→11 Δ%': f"{row['pop_change_2006_2011_pct']*100:.1f}%",
        '2016 Pop': f"{int(row['population_2016']):,}",
        '2016 Den': f"{row['density_2016']:.1f}",
        '11→16 Δ%': f"{row['pop_change_2011_2016_pct']*100:.1f}%",
        '2021 Pop': f"{int(row['population_2021']):,}",
        '2021 Den': f"{row['density_2021']:.1f}",
        '16→21 Δ%': f"{row['pop_change_2016_2021_pct']*100:.1f}%",
        'Overall Δ%': f"{row['overall_growth_pct']:.1f}%"
    })

display_df = pd.DataFrame(display_data)

gt = (
    GT(display_df)
    .tab_header(
        title="Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Population Growth and Density Changes (1996-2021)"
    )
    .tab_spanner(label="1996", columns=['1996 Pop', '1996 Den'])
    .tab_spanner(label="2001", columns=['2001 Pop', '2001 Den'])
    .tab_spanner(label="2006", columns=['2006 Pop', '2006 Den'])
    .tab_spanner(label="2011", columns=['2011 Pop', '2011 Den'])
    .tab_spanner(label="2016", columns=['2016 Pop', '2016 Den'])
    .tab_spanner(label="2021", columns=['2021 Pop', '2021 Den'])
    .cols_label(
        **{
            'Town': 'Town',
            '1996 Pop': 'Pop', '1996 Den': 'Dens',
            '2001 Pop': 'Pop', '2001 Den': 'Dens',
            '2006 Pop': 'Pop', '2006 Den': 'Dens',
            '2011 Pop': 'Pop', '2011 Den': 'Dens',
            '2016 Pop': 'Pop', '2016 Den': 'Dens',
            '2021 Pop': 'Pop', '2021 Den': 'Dens',
            '96→01 Δ%': '5yr Δ%',
            '01→06 Δ%': '5yr Δ%',
            '06→11 Δ%': '5yr Δ%',
            '11→16 Δ%': '5yr Δ%',
            '16→21 Δ%': '5yr Δ%',
            'Overall Δ%': 'Total Δ%'
        }
    )
    .opt_align_table_header(align='center')
    .tab_options(
        container_width='100%',
        table_font_size='sm'
    )
)

gt.gtsave('table.png')
print("✓ Table saved to table.png")
