import sys
sys.path.insert(0, '.claude/skills/great-tables-ci/scripts')

import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band

# Step 1: Load and clean data
df_raw = pd.read_csv('towny.csv')

# Filter to valid towns (population > 0 in 1996)
df_valid = df_raw[(df_raw['population_1996'].notna()) & (df_raw['population_1996'] > 0)].copy()

# Calculate overall growth
df_valid['overall_growth_pct'] = (
    (df_valid['population_2021'] - df_valid['population_1996']) / df_valid['population_1996'] * 100
)

# Get top 15 fastest-growing towns
top_15 = df_valid.nlargest(15, 'overall_growth_pct').reset_index(drop=True)

# Step 2: Prepare display dataframe with selected columns
display_cols = ['name', 'population_1996', 'population_2001', 'population_2006',
                'population_2011', 'population_2016', 'population_2021',
                'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct',
                'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']

df_display = top_15[display_cols].copy()

# Rename columns for display
df_display.columns = ['Town', 'Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021',
                      'Chg 96-01 %', 'Chg 01-06 %', 'Chg 06-11 %', 'Chg 11-16 %', 'Chg 16-21 %',
                      'Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021']

# Ensure numeric columns are float
pop_cols = ['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021']
pct_cols = ['Chg 96-01 %', 'Chg 01-06 %', 'Chg 06-11 %', 'Chg 11-16 %', 'Chg 16-21 %']
den_cols = ['Den 1996', 'Den 2001', 'Den 2006', 'Den 2011', 'Den 2016', 'Den 2021']

for col in pop_cols + pct_cols + den_cols:
    df_display[col] = pd.to_numeric(df_display[col], errors='coerce')

# Step 3: Identify colored measures (Big Color)
# Per palettes.md: max 2 colored measures. Population and percentage change are primary.
# Population: neutral magnitude → Blues (sequential)
# Percentage change: signed values (can be pos or neg) → RdYlGn (diverging, default)

pop_cols_to_color = ['Pop 1996', 'Pop 2021']  # Color only endpoints to show range
pct_cols_to_color = pct_cols  # Color all percentage change columns (second colored measure)

# Step 4 & 5: Build the table with heading band and small color
gt = (
    GT(df_display, rowname_col='Town')
    # Format population columns
    .fmt_number(columns=pop_cols, decimals=0, use_seps=True)
    # Format percentage change columns
    .fmt_percent(columns=pct_cols, decimals=1, scale_values=False)
    # Format density columns (no color)
    .fmt_number(columns=den_cols, decimals=2, use_seps=False)
    # Colored measure 1: Population (first and last census year)
    .data_color(
        columns=pop_cols_to_color,
        palette=PALETTE['sequential']['neutral'],
        domain=[float(np.nanmin(df_display[pop_cols].to_numpy())),
                float(np.nanmax(df_display[pop_cols].to_numpy()))],
        truncate=False,
        na_color=PALETTE['neutral']['na_cell'],
    )
    # Colored measure 2: Percentage change (signed, diverging)
    .data_color(
        columns=pct_cols_to_color,
        palette=PALETTE['diverging']['default'],
        domain=[-max(abs(float(np.nanmin(df_display[pct_cols].to_numpy()))),
                     abs(float(np.nanmax(df_display[pct_cols].to_numpy())))),
                max(abs(float(np.nanmin(df_display[pct_cols].to_numpy()))),
                    abs(float(np.nanmax(df_display[pct_cols].to_numpy()))))],
        truncate=False,
        na_color=PALETTE['neutral']['na_cell'],
    )
    # Column spanners to group columns by measure
    .tab_spanner(label='Population', columns=pop_cols)
    .tab_spanner(label='Population Change %', columns=pct_cols)
    .tab_spanner(label='Density (people/km²)', columns=den_cols)
    # Heading band - light band because we have Big Color
    .tab_options(
        column_labels_background_color=PALETTE['washed']['navy'],
        column_labels_border_bottom_color=PALETTE['neutral']['column_label_rule'],
        column_labels_border_bottom_width='2px',
    )
    # Cell borders (Step 5a)
    .tab_options(
        table_body_hlines_style='solid',
        table_body_hlines_color=PALETTE['neutral']['hairline'],
        table_body_hlines_width='1px',
    )
    # Column group vertical dividers (Step 5b)
    .tab_style(
        style=style.borders(sides='right', color=PALETTE['neutral']['vertical_divider'], weight='1px'),
        locations=loc.body(columns='Pop 2021'),
    )
    .tab_style(
        style=style.borders(sides='right', color=PALETTE['neutral']['vertical_divider'], weight='1px'),
        locations=loc.column_labels(columns='Pop 2021'),
    )
    .tab_style(
        style=style.borders(sides='right', color=PALETTE['neutral']['vertical_divider'], weight='1px'),
        locations=loc.body(columns='Chg 16-21 %'),
    )
    .tab_style(
        style=style.borders(sides='right', color=PALETTE['neutral']['vertical_divider'], weight='1px'),
        locations=loc.column_labels(columns='Chg 16-21 %'),
    )
    # Row striping (Step 5c)
    .opt_row_striping()
    # Stub tint (Step 5d) - washed Navy to match Big Color
    .tab_style(
        style=style.fill(color=PALETTE['washed']['navy']),
        locations=loc.stub(),
    )
    # Frame (Step 5 - global constant)
    .tab_options(
        table_border_top_style='solid',
        table_border_top_color=PALETTE['neutral']['column_label_rule'],
        table_border_top_width='1px',
        table_border_bottom_style='solid',
        table_border_bottom_color=PALETTE['neutral']['column_label_rule'],
        table_border_bottom_width='1px',
        table_border_left_style='solid',
        table_border_left_color=PALETTE['neutral']['column_label_rule'],
        table_border_left_width='1px',
        table_border_right_style='solid',
        table_border_right_color=PALETTE['neutral']['column_label_rule'],
        table_border_right_width='1px',
    )
    # Titles and annotations
    .tab_header(
        title='Ontario\'s 15 Fastest-Growing Towns (1996–2021)',
        subtitle='Population growth, density changes, and period-to-period percentage changes across all census years'
    )
    .tab_source_note(
        md('**Source:** Statistics Canada Census data (1996–2021) | **Measure:** Population density is persons per km²')
    )
)

# Step 7: Render
gt.gtsave('table.png', expand=15, zoom=2.0)
