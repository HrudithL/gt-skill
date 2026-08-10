import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_rate'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 by overall growth rate
top_15 = df.nlargest(15, 'overall_growth_rate').copy()

# Select and organize columns
columns_to_use = ['name',
                  'population_1996', 'density_1996',
                  'population_2001', 'density_2001', 'pop_change_1996_2001_pct',
                  'population_2006', 'density_2006', 'pop_change_2001_2006_pct',
                  'population_2011', 'density_2011', 'pop_change_2006_2011_pct',
                  'population_2016', 'density_2016', 'pop_change_2011_2016_pct',
                  'population_2021', 'density_2021', 'pop_change_2016_2021_pct']

display_data = top_15[columns_to_use].reset_index(drop=True)

# Rename columns for readability
display_data.columns = ['Town',
                        'Pop_1996', 'Density_1996',
                        'Pop_2001', 'Density_2001', 'Change_1996_2001',
                        'Pop_2006', 'Density_2006', 'Change_2001_2006',
                        'Pop_2011', 'Density_2011', 'Change_2006_2011',
                        'Pop_2016', 'Density_2016', 'Change_2011_2016',
                        'Pop_2021', 'Density_2021', 'Change_2016_2021']

# Create the GT table
gt = GT(display_data, rowname_col='Town')

gt = gt.tab_header(
    title="Population Growth Trends — Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Population and population density across census years (1996–2021), with percentage change between each period")
)

# Add spanners for census year groupings
gt = gt.tab_spanner(label="1996", columns=['Pop_1996', 'Density_1996'])
gt = gt.tab_spanner(label="2001", columns=['Pop_2001', 'Density_2001', 'Change_1996_2001'])
gt = gt.tab_spanner(label="2006", columns=['Pop_2006', 'Density_2006', 'Change_2001_2006'])
gt = gt.tab_spanner(label="2011", columns=['Pop_2011', 'Density_2011', 'Change_2006_2011'])
gt = gt.tab_spanner(label="2016", columns=['Pop_2016', 'Density_2016', 'Change_2011_2016'])
gt = gt.tab_spanner(label="2021", columns=['Pop_2021', 'Density_2021', 'Change_2016_2021'])

# Format numbers
gt = gt.fmt_integer(columns=['Pop_1996', 'Pop_2001', 'Pop_2006', 'Pop_2011', 'Pop_2016', 'Pop_2021'])
gt = gt.fmt_number(columns=['Density_1996', 'Density_2001', 'Density_2006', 'Density_2011', 'Density_2016', 'Density_2021'], decimals=2)

# Format percentage changes with sign
gt = gt.fmt_percent(
    columns=['Change_1996_2001', 'Change_2001_2006', 'Change_2006_2011', 'Change_2011_2016', 'Change_2016_2021'],
    decimals=1,
    scale_values=False,
    force_sign=True
)

# Handle missing values
gt = gt.sub_missing(columns=['Change_1996_2001', 'Change_2001_2006', 'Change_2006_2011', 'Change_2011_2016', 'Change_2016_2021'], missing_text="—")

# Apply heatmap to density changes - the hero measure showing density evolution
density_cols = ['Density_1996', 'Density_2001', 'Density_2006', 'Density_2011', 'Density_2016', 'Density_2021']
gt = heatmap(gt, density_cols, kind="sequential", hue="positive")

# Apply humanized labels
gt = humanize_labels(
    gt,
    display_data,
    overrides={
        'Pop_1996': 'Population', 'Density_1996': 'Density',
        'Pop_2001': 'Population', 'Density_2001': 'Density', 'Change_1996_2001': 'Change %',
        'Pop_2006': 'Population', 'Density_2006': 'Density', 'Change_2001_2006': 'Change %',
        'Pop_2011': 'Population', 'Density_2011': 'Density', 'Change_2006_2011': 'Change %',
        'Pop_2016': 'Population', 'Density_2016': 'Density', 'Change_2011_2016': 'Change %',
        'Pop_2021': 'Population', 'Density_2021': 'Density', 'Change_2016_2021': 'Change %',
    }
)

# Apply styling
gt = band(gt, hue="forest")
gt = stub_tint(gt, hue="forest")
gt = stripe(gt)
gt = hairlines(gt)
gt = frame(gt)

gt = gt.tab_source_note(source_note="Source: Statistics Canada Census data (1996–2021). Ranked by total population growth rate. Density in persons per km².")

finalize(gt, path="table.png")
