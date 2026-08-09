import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_1996_2021'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_1996_2021').copy()

# Select and organize columns for the table
display_df = top_15[[
    'name',
    'population_1996', 'density_1996',
    'population_2001', 'density_2001', 'pop_change_1996_2001_pct',
    'population_2006', 'density_2006', 'pop_change_2001_2006_pct',
    'population_2011', 'density_2011', 'pop_change_2006_2011_pct',
    'population_2016', 'density_2016', 'pop_change_2011_2016_pct',
    'population_2021', 'density_2021', 'pop_change_2016_2021_pct',
]].reset_index(drop=True)

# Rename columns for display
display_df.columns = [
    'town',
    'pop_1996', 'dens_1996',
    'pop_2001', 'dens_2001', 'chg_1996_01',
    'pop_2006', 'dens_2006', 'chg_2001_06',
    'pop_2011', 'dens_2011', 'chg_2006_11',
    'pop_2016', 'dens_2016', 'chg_2011_16',
    'pop_2021', 'dens_2021', 'chg_2016_21',
]

# Create the GT table
gt = GT(display_df, rowname_col='town')

# Add title and subtitle
gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Population and density changes across census years 1996–2021, with period-to-period growth rates")
)

# Add spanners for each census period
gt = gt.tab_spanner(label="1996", columns=['pop_1996', 'dens_1996'])
gt = gt.tab_spanner(label="2001", columns=['pop_2001', 'dens_2001', 'chg_1996_01'])
gt = gt.tab_spanner(label="2006", columns=['pop_2006', 'dens_2006', 'chg_2001_06'])
gt = gt.tab_spanner(label="2011", columns=['pop_2011', 'dens_2011', 'chg_2006_11'])
gt = gt.tab_spanner(label="2016", columns=['pop_2016', 'dens_2016', 'chg_2011_16'])
gt = gt.tab_spanner(label="2021", columns=['pop_2021', 'dens_2021', 'chg_2016_21'])

# Format numbers: populations as integers with thousands separator
for col in ['pop_1996', 'pop_2001', 'pop_2006', 'pop_2011', 'pop_2016', 'pop_2021']:
    gt = gt.fmt_integer(columns=col, use_seps=True)

# Format densities with 1 decimal place
for col in ['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021']:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format percentage changes with 1 decimal place
for col in ['chg_1996_01', 'chg_2001_06', 'chg_2006_11', 'chg_2011_16', 'chg_2016_21']:
    gt = gt.fmt_percent(columns=col, decimals=1)

# Apply humanized labels
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        'pop_1996': 'Pop',
        'dens_1996': 'Density',
        'pop_2001': 'Pop',
        'dens_2001': 'Density',
        'chg_1996_01': '% Change',
        'pop_2006': 'Pop',
        'dens_2006': 'Density',
        'chg_2001_06': '% Change',
        'pop_2011': 'Pop',
        'dens_2011': 'Density',
        'chg_2006_11': '% Change',
        'pop_2016': 'Pop',
        'dens_2016': 'Density',
        'chg_2011_16': '% Change',
        'pop_2021': 'Pop',
        'dens_2021': 'Density',
        'chg_2016_21': '% Change',
    }
)

# Apply heatmap to percentage changes (the key measure showing growth trends)
change_cols = ['chg_1996_01', 'chg_2001_06', 'chg_2006_11', 'chg_2011_16', 'chg_2016_21']
gt = heatmap(gt, change_cols, kind='diverging', hue='default')

# Apply band, stripe, stub tint with forest hue (growth theme)
gt = band(gt, hue='forest')
gt = stripe(gt)
gt = stub_tint(gt, hue='forest')

# Add source note
gt = gt.tab_source_note(source_note="Source: Statistics Canada Census data 1996–2021")

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt, path='table.png')
