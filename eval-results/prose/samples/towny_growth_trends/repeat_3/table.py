import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Load data
df = pd.read_csv('towny.csv')

# Calculate overall growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct').reset_index(drop=True)

# Build display dataframe
display_df = pd.DataFrame()
display_df['Town'] = top_15['name']

# Density columns
display_df['dens_1996'] = top_15['density_1996']
display_df['dens_2001'] = top_15['density_2001']
display_df['dens_2006'] = top_15['density_2006']
display_df['dens_2011'] = top_15['density_2011']
display_df['dens_2016'] = top_15['density_2016']
display_df['dens_2021'] = top_15['density_2021']

# Percent change columns
display_df['pct_96_01'] = (top_15['pop_change_1996_2001_pct'] * 100)
display_df['pct_01_06'] = (top_15['pop_change_2001_2006_pct'] * 100)
display_df['pct_06_11'] = (top_15['pop_change_2006_2011_pct'] * 100)
display_df['pct_11_16'] = (top_15['pop_change_2011_2016_pct'] * 100)
display_df['pct_16_21'] = (top_15['pop_change_2016_2021_pct'] * 100)

# Ensure all numeric columns are float
numeric_cols = ['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021',
                'pct_96_01', 'pct_01_06', 'pct_06_11', 'pct_11_16', 'pct_16_21']
for col in numeric_cols:
    display_df[col] = pd.to_numeric(display_df[col], errors='coerce')

# Create GT object
gt = (
    GT(display_df, rowname_col='Town')
    .tab_spanner(label='Population Density (persons/km²)', columns=['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021'])
    .tab_spanner(label='Population % Change Between Periods', columns=['pct_96_01', 'pct_01_06', 'pct_06_11', 'pct_11_16', 'pct_16_21'])
    .cols_label(
        dens_1996='1996',
        dens_2001='2001',
        dens_2006='2006',
        dens_2011='2011',
        dens_2016='2016',
        dens_2021='2021',
        pct_96_01='1996–2001',
        pct_01_06='2001–2006',
        pct_06_11='2006–2011',
        pct_11_16='2011–2016',
        pct_16_21='2016–2021',
    )
    .fmt_number(columns=['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021'], decimals=1, use_seps=True)
    .fmt_percent(columns=['pct_96_01', 'pct_01_06', 'pct_06_11', 'pct_11_16', 'pct_16_21'], decimals=1, scale_values=False, force_sign=True)
    .data_color(
        columns=['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021'],
        palette='Blues',
        domain=[float(np.nanmin(display_df[['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021']].to_numpy())),
                float(np.nanmax(display_df[['dens_1996', 'dens_2001', 'dens_2006', 'dens_2011', 'dens_2016', 'dens_2021']].to_numpy()))],
        truncate=False,
        na_color='#808080',
    )
    .data_color(
        columns=['pct_96_01', 'pct_01_06', 'pct_06_11', 'pct_11_16', 'pct_16_21'],
        palette='RdYlGn',
        domain=[-100, 100],
        truncate=False,
        na_color='#808080',
    )
    .tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.body(columns='dens_2021'),
    )
    .tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.column_labels(columns='dens_2021'),
    )
    .tab_options(
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px',
        table_border_top_style='solid',
        table_border_top_color='#CCCCCC',
        table_border_top_width='1px',
        table_border_bottom_style='solid',
        table_border_bottom_color='#CCCCCC',
        table_border_bottom_width='1px',
        table_border_left_style='solid',
        table_border_left_color='#CCCCCC',
        table_border_left_width='1px',
        table_border_right_style='solid',
        table_border_right_color='#CCCCCC',
        table_border_right_width='1px',
        heading_padding='6px',
        column_labels_padding='6px',
        column_labels_padding_horizontal='8px',
        data_row_padding='5px',
        data_row_padding_horizontal='8px',
        source_notes_padding='6px',
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color='#EAF0F6'),
        locations=loc.stub(),
    )
    .cols_width(cases={
        'dens_1996': '90px',
        'dens_2001': '90px',
        'dens_2006': '90px',
        'dens_2011': '90px',
        'dens_2016': '90px',
        'dens_2021': '90px',
        'pct_96_01': '85px',
        'pct_01_06': '85px',
        'pct_06_11': '85px',
        'pct_11_16': '85px',
        'pct_16_21': '85px',
    })
    .tab_header(
        title='Population Growth Trends: Top 15 Fastest-Growing Ontario Towns',
        subtitle='Density and Population Changes Across Census Years (1996–2021)',
    )
    .tab_source_note(source_note='Fastest-growing towns identified by largest percent population increase from 1996 to 2021. Density measured as population per square kilometer.')
    .tab_source_note(source_note='Source: Statistics Canada Census subdivisions, 1996–2021.')
)

gt.gtsave('table.png', expand=15)
print("Table saved to table.png")
