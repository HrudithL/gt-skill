import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Read and clean data
df = pd.read_csv('towny.csv')

# Calculate total population growth 1996-2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Get top 15 fastest growing towns
top_15 = df.nlargest(15, 'total_growth_pct').reset_index(drop=True).copy()

# Step 2: Organize columns for display
# Build display dataframe with town name and density data
display_df = pd.DataFrame({
    'Town': top_15['name'].values,
    'density_1996': top_15['density_1996'].round(2).values,
    'density_2001': top_15['density_2001'].round(2).values,
    'density_2006': top_15['density_2006'].round(2).values,
    'density_2011': top_15['density_2011'].round(2).values,
    'density_2016': top_15['density_2016'].round(2).values,
    'density_2021': top_15['density_2021'].round(2).values,
    'pct_change_1996_2001': top_15['pop_change_1996_2001_pct'].values,
    'pct_change_2001_2006': top_15['pop_change_2001_2006_pct'].values,
    'pct_change_2006_2011': top_15['pop_change_2006_2011_pct'].values,
    'pct_change_2011_2016': top_15['pop_change_2011_2016_pct'].values,
    'pct_change_2016_2021': top_15['pop_change_2016_2021_pct'].values,
})

# Convert percentage columns to decimal form for fmt_percent
pct_cols = ['pct_change_1996_2001', 'pct_change_2001_2006', 'pct_change_2006_2011',
            'pct_change_2011_2016', 'pct_change_2016_2021']
for col in pct_cols:
    display_df[col] = display_df[col].astype(float)

# Compute domains for heatmaps
density_cols = ['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']
density_min = float(np.nanmin(display_df[density_cols].to_numpy()))
density_max = float(np.nanmax(display_df[density_cols].to_numpy()))

pct_min = float(np.nanmin(display_df[pct_cols].to_numpy()))
pct_max = float(np.nanmax(display_df[pct_cols].to_numpy()))

# Step 3: Build the GT table
gt = (
    GT(display_df, rowname_col='Town')
    # Format columns
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=pct_cols, decimals=1, scale_values=False)

    # Step 3: Apply color fills - density as sequential (neutral magnitude = Blues)
    .data_color(
        columns=density_cols,
        palette='Blues',
        domain=[density_min, density_max],
        truncate=False,
        na_color='#808080',
    )

    # Percentage changes as diverging (positive and negative both present)
    .data_color(
        columns=pct_cols,
        palette='RdYlGn',
        domain=[pct_min, pct_max],
        truncate=False,
        na_color='#808080',
    )

    # Column spanners to organize the measures
    .tab_spanner(label='Population Density (per km²)', columns=density_cols)
    .tab_spanner(label='Population Change (%)', columns=pct_cols)

    # Step 4: Apply heading band
    .pipe(band)

    # Step 5: Apply small color elements
    .pipe(stripe)
    .pipe(stub_tint)
    .pipe(hairlines)

    # Column-group vertical dividers
    .tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.body(columns='density_2021'),
    )
    .tab_style(
        style=style.borders(sides='right', color='#D0D0D0', weight='1px'),
        locations=loc.column_labels(columns='density_2021'),
    )

    # Column widths for compact layout
    .cols_width(cases={
        'Town': '140px',
        'density_1996': '100px',
        'density_2001': '100px',
        'density_2006': '100px',
        'density_2011': '100px',
        'density_2016': '100px',
        'density_2021': '100px',
        'pct_change_1996_2001': '95px',
        'pct_change_2001_2006': '95px',
        'pct_change_2006_2011': '95px',
        'pct_change_2011_2016': '95px',
        'pct_change_2016_2021': '95px',
    })

    # Tab options for layout and spacing
    .tab_options(
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px',
        table_font_size='11px',
        heading_padding='12px',
        column_labels_padding='8px',
        column_labels_padding_horizontal='6px',
        data_row_padding='4px',
        data_row_padding_horizontal='6px',
        source_notes_padding='8px',
    )

    # Titles and annotations
    .tab_header(
        title='Ontario\'s Fastest-Growing Towns (1996–2021)',
        subtitle='Population Density and Growth Rates Across Census Periods'
    )

    .tab_source_note(
        'Population density shows the trend of residential intensity (per km²) across all six census years from 1996 to 2021. '
        'Percentage changes represent the intercensal population growth rate for each five-year period. '
        'Towns are ranked by total population growth from 1996 to 2021.'
    )

    .tab_source_note(
        'Source: Statistics Canada Census of Population, 1996–2021'
    )

    # Step 5: Frame
    .pipe(frame)
)

# Step 7: Render
finalize(gt, 'table.png')
