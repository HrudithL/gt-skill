import pandas as pd
from great_tables import GT, md, html, style, loc
import sys
sys.path.insert(0, '/Users/hrudithl/Documents/posit-dev/gtskill/.claude/worktrees/skill-quality-fixes/runs/sweep/20260808_184920_house_6prompts/prompts/towny_growth_trends/repeat_1/.claude/skills/great-tables-house')
from house_table import PALETTE, frame, finalize, heatmap

df = pd.read_csv('towny.csv')

# Calculate overall growth rate (1996-2021)
df['overall_growth'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns (by overall growth rate)
top_15 = df.nlargest(15, 'overall_growth')

# Select relevant columns: name, then density for each census year, then % change between periods
display_data = top_15[[
    'name',
    'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
    'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct'
]].reset_index(drop=True)

# Format for display
display_data = display_data.copy()
display_data['rank'] = range(1, 16)
display_data = display_data[['rank', 'name', 'density_1996', 'density_2001', 'density_2006',
                             'density_2011', 'density_2016', 'density_2021',
                             'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
                             'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
                             'pop_change_2016_2021_pct']]

# Rename columns for clarity
display_data.columns = [
    'Rank', 'Town',
    'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021',
    'Change 1996-01 %', 'Change 2001-06 %', 'Change 2006-11 %', 'Change 2011-16 %', 'Change 2016-21 %'
]

gt = GT(display_data)

# Title and subtitle
gt = gt.tab_header(
    title='Top 15 Fastest-Growing Ontario Towns (1996-2021)',
    subtitle='Population Density Trends and Period-over-Period Growth Rates'
)

# Format rank as integer
gt = gt.fmt_integer(columns='Rank')

# Format density columns (2 decimal places)
density_cols = ['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021']
for col in density_cols:
    gt = gt.fmt_number(columns=col, decimals=2)

# Format percentage change columns
pct_cols = ['Change 1996-01 %', 'Change 2001-06 %', 'Change 2006-11 %', 'Change 2011-16 %', 'Change 2016-21 %']
for col in pct_cols:
    gt = gt.fmt_percent(columns=col, decimals=1)

# Color the density columns with a heatmap (blue scale for magnitude/volume)
gt = heatmap(gt, density_cols, kind='sequential', hue='neutral')

# Color the percentage change columns (second heatmap - diverging for growth/decline)
gt = heatmap(gt, pct_cols, kind='diverging', hue='default')

# Add row hairlines
gt = gt.tab_options(table_body_hlines_style='solid', table_body_hlines_width='1px', table_body_hlines_color='#EEEEEE')

# Add source notes
gt = gt.tab_source_note('Source: Provided dataset (census data 1996-2021)')
gt = gt.tab_source_note('Fastest-growing towns ranked by overall population growth rate (1996-2021). Density measured in persons per km². Percentage changes calculated period-over-period.')

# Frame
gt = frame(gt)

# Finalize
finalize(gt, path='table.png', zoom=2.0, expand=15)
