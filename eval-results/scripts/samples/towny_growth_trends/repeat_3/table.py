import pandas as pd
from great_tables import GT, md, html, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
import sys
sys.path.insert(0, '.claude/skills/great-tables-ci/scripts')

# Load and prepare data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_pct'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')[['name', 'density_1996', 'density_2001',
                                                   'density_2006', 'density_2011', 'density_2016',
                                                   'density_2021', 'pop_change_1996_2001_pct',
                                                   'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                                                   'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct',
                                                   'overall_growth_pct']].reset_index(drop=True)

# Rename columns for display
top_15_display = top_15.copy()
top_15_display.columns = ['Town', 'Density 1996', 'Density 2001', 'Density 2006',
                           'Density 2011', 'Density 2016', 'Density 2021',
                           'Change 96-01 %', 'Change 01-06 %', 'Change 06-11 %',
                           'Change 11-16 %', 'Change 16-21 %', 'Overall Growth %']

# Create the table
gt = (
    GT(top_15_display, rowname_col='Town')
    .fmt_number(columns=['Density 1996', 'Density 2001', 'Density 2006',
                         'Density 2011', 'Density 2016', 'Density 2021'],
                decimals=2)
    .fmt_percent(columns=['Change 96-01 %', 'Change 01-06 %', 'Change 06-11 %',
                          'Change 11-16 %', 'Change 16-21 %', 'Overall Growth %'],
                 decimals=1, scale_values=False, force_sign=True)
    .cols_width(cases={'Town': '200px', 'Density 1996': '100px', 'Density 2001': '100px',
                       'Density 2006': '100px', 'Density 2011': '100px', 'Density 2016': '100px',
                       'Density 2021': '100px', 'Change 96-01 %': '90px', 'Change 01-06 %': '90px',
                       'Change 06-11 %': '90px', 'Change 11-16 %': '90px', 'Change 16-21 %': '90px',
                       'Overall Growth %': '110px'})
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density and Growth Trends (1996-2021)"
    )
    .tab_options(
        heading_padding='6px',
        column_labels_padding='6px',
        column_labels_padding_horizontal='8px',
        data_row_padding='5px',
        data_row_padding_horizontal='8px',
        source_notes_padding='6px',
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px'
    )
)

# Add heatmap for density columns (sequential)
gt = heatmap(gt, columns=['Density 1996', 'Density 2001', 'Density 2006',
                          'Density 2011', 'Density 2016', 'Density 2021'],
             kind='sequential', hue='neutral')

# Add diverging heatmap for percentage change columns
gt = heatmap(gt, columns=['Change 96-01 %', 'Change 01-06 %', 'Change 06-11 %',
                          'Change 11-16 %', 'Change 16-21 %', 'Overall Growth %'],
             kind='diverging', hue='default')

# Apply branding
gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Add footer notes
gt = (
    gt
    .tab_source_note(
        source_note="Fastest-growing means highest percent population change from 1996–2021."
    )
    .tab_source_note(
        source_note="Source: towny.csv | Density measured in persons per km²"
    )
)

# Finalize and render
gt = finalize(gt, path='table.png')
