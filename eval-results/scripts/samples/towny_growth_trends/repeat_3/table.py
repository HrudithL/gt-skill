import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint, hairlines

# Step 1: Read and clean data
df_raw = pd.read_csv('towny.csv')

# Calculate overall growth from 1996 to 2021
df_raw['overall_growth'] = ((df_raw['population_2021'] - df_raw['population_1996']) / df_raw['population_1996'] * 100)

# Get top 15 fastest-growing towns
df = df_raw.nlargest(15, 'overall_growth')[
    ['name', 'population_1996', 'population_2001', 'population_2006',
     'population_2011', 'population_2016', 'population_2021',
     'density_1996', 'density_2001', 'density_2006',
     'density_2011', 'density_2016', 'density_2021',
     'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct',
     'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct',
     'pop_change_2016_2021_pct']
].reset_index(drop=True)

# Rename columns for clarity
df = df.rename(columns={
    'name': 'Town',
    'population_1996': 'Pop 1996',
    'population_2001': 'Pop 2001',
    'population_2006': 'Pop 2006',
    'population_2011': 'Pop 2011',
    'population_2016': 'Pop 2016',
    'population_2021': 'Pop 2021',
    'density_1996': 'Den 1996',
    'density_2001': 'Den 2001',
    'density_2006': 'Den 2006',
    'density_2011': 'Den 2011',
    'density_2016': 'Den 2016',
    'density_2021': 'Den 2021',
    'pop_change_1996_2001_pct': 'Change 96-01 %',
    'pop_change_2001_2006_pct': 'Change 01-06 %',
    'pop_change_2006_2011_pct': 'Change 06-11 %',
    'pop_change_2011_2016_pct': 'Change 11-16 %',
    'pop_change_2016_2021_pct': 'Change 16-21 %',
})

# Step 2: Organize columns with stub
density_cols = ['Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021']
pct_change_cols = ['Change 96-01 %', 'Change 01-06 %', 'Change 06-11 %', 'Change 11-16 %', 'Change 16-21 %']

# Step 3: Compute Big Color domains
density_vals = df[density_cols].to_numpy()
density_lo = float(np.nanmin(density_vals))
density_hi = float(np.nanmax(density_vals))

pct_vals = df[pct_change_cols].to_numpy()
pct_lo = float(np.nanmin(pct_vals))
pct_hi = float(np.nanmax(pct_vals))
pct_sym = max(abs(pct_lo), abs(pct_hi))

# Build table
gt = (
    GT(df, rowname_col='Town')
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_change_cols, decimals=1, scale_values=False, force_sign=True)
    .tab_spanner(label='Population Density (persons/km2)', columns=density_cols)
    .tab_spanner(label='Period-over-Period Change (%)', columns=pct_change_cols)
    .data_color(
        columns=density_cols,
        palette='Blues',
        domain=[density_lo, density_hi],
        truncate=False,
        na_color='#808080',
    )
    .data_color(
        columns=pct_change_cols,
        palette='RdYlGn',
        domain=[-pct_sym, pct_sym],
        truncate=False,
        na_color='#808080',
    )
)

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = hairlines(gt)

# Column-group vertical dividers
gt = (
    gt.tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.body(columns='Den 2021'),
    )
    .tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.column_labels(columns='Den 2021'),
    )
)

gt = stripe(gt)
gt = stub_tint(gt)

# Compact layout with column width sizing and padding
gt = (
    gt.cols_width(cases={
        'Town': '160px',
        'Den 1996': '90px',
        'Den 2001': '90px',
        'Den 2006': '90px',
        'Den 2011': '90px',
        'Den 2016': '90px',
        'Den 2021': '90px',
        'Change 96-01 %': '85px',
        'Change 01-06 %': '85px',
        'Change 06-11 %': '85px',
        'Change 11-16 %': '85px',
        'Change 16-21 %': '85px',
    })
    .tab_options(
        heading_padding='6px',
        column_labels_padding='6px',
        column_labels_padding_horizontal='8px',
        data_row_padding='5px',
        data_row_padding_horizontal='8px',
        source_notes_padding='6px',
    )
)

# Step 6: Titles and annotations
gt = (
    gt.tab_header(
        title="Ontario's 15 Fastest-Growing Towns (1996-2021)",
        subtitle='Population density trends across Census periods, with percentage change between each period'
    )
    .tab_source_note(
        'Fastest-growing means highest percent increase from 1996 to 2021 population baseline. Density measured in persons per km2. Period changes show percent growth/decline between consecutive Census years (1996 to 2001, 2001 to 2006, etc.).'
    )
    .tab_source_note(
        'Source: Statistics Canada Census subdivisions, 1996-2021 Census data (towny.csv)'
    )
)

# Frame and finalize (finalize includes gtsave)
gt = frame(gt)
finalize(gt)
