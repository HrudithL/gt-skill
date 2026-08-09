import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load and prepare data
df = pd.read_csv('towny.csv')

# Calculate overall population growth 1996-2021
df['overall_growth'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns by overall population growth
top_15 = df.dropna(subset=['overall_growth']).nlargest(15, 'overall_growth')[['name', 'population_1996', 'population_2001',
                                               'population_2006', 'population_2011', 'population_2016',
                                               'population_2021', 'density_1996', 'density_2001',
                                               'density_2006', 'density_2011', 'density_2016', 'density_2021']].copy()

# Calculate density change percentages between each period
top_15['density_change_1996_2001_pct'] = np.where(
    top_15['density_1996'] > 0,
    (top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996'],
    None
)
top_15['density_change_2001_2006_pct'] = np.where(
    top_15['density_2001'] > 0,
    (top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001'],
    None
)
top_15['density_change_2006_2011_pct'] = np.where(
    top_15['density_2006'] > 0,
    (top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006'],
    None
)
top_15['density_change_2011_2016_pct'] = np.where(
    top_15['density_2011'] > 0,
    (top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011'],
    None
)
top_15['density_change_2016_2021_pct'] = np.where(
    top_15['density_2021'] > 0,
    (top_15['density_2021'] - top_15['density_2016']) / top_15['density_2021'],
    None
)

# Select columns to display
display_cols = ['name', 'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
                'density_change_1996_2001_pct', 'density_change_2001_2006_pct', 'density_change_2006_2011_pct',
                'density_change_2011_2016_pct', 'density_change_2016_2021_pct']

table_data = top_15[display_cols].copy()

# Rename columns for clarity
table_data.columns = ['Town', 'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021',
                      'Change 1996–2001', 'Change 2001–2006', 'Change 2006–2011', 'Change 2011–2016', 'Change 2016–2021']

# Create GT table
gt = GT(table_data, rowname_col='Town')

# Format density columns as numbers with 2 decimals
gt = gt.fmt_number(columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'], decimals=2)

# Format percentage change columns
gt = gt.fmt_percent(columns=['Change 1996–2001', 'Change 2001–2006', 'Change 2006–2011', 'Change 2011–2016', 'Change 2016–2021'],
                    decimals=1, scale_values=False)

# Replace missing values
gt = gt.sub_missing(missing_text='—')

# Add column spanners for density and change periods
gt = gt.tab_spanner(label='Population Density (per km²)', columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'])
gt = gt.tab_spanner(label='Density % Change Between Periods', columns=['Change 1996–2001', 'Change 2001–2006', 'Change 2006–2011', 'Change 2011–2016', 'Change 2016–2021'])

# Add title and subtitle
gt = gt.tab_header(
    title='Ontario Towns: Population Density Growth Trends',
    subtitle='Top 15 fastest-growing municipalities by overall population growth (1996–2021), ranked by overall population growth rate'
)

# Apply heading band
gt = gt.tab_options(
    column_labels_background_color='#C9E0F0',
    column_labels_border_bottom_color='#CCCCCC',
    column_labels_border_bottom_width='2px',
    column_labels_border_bottom_style='solid',
)

# Add row hairlines
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color='#E8E8E8',
    table_body_hlines_width='1px',
)

# Apply frame
gt = frame(gt)

# Apply striping (since we have 15 rows)
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue='navy')

# Apply heatmap to density change percentages
change_cols = ['Change 1996–2001', 'Change 2001–2006', 'Change 2006–2011', 'Change 2011–2016', 'Change 2016–2021']
gt = heatmap(gt, change_cols, kind='diverging', hue='default')

# Add source notes
gt = gt.tab_source_note(
    source_note='Density change percentages computed continuously between adjacent census periods (5-year intervals).'
)
gt = gt.tab_source_note(
    source_note='Source: Ontario census data (1996–2021); towns ranked by overall population growth rate (1996–2021).'
)

# Finalize and save
finalize(gt, path='table.png', zoom=2.0, expand=15)
