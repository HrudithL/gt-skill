import pandas as pd
from great_tables import GT, md, html, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("towny.csv")

# Calculate overall population growth from 1996 to 2021
df['pop_growth_1996_2021'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'pop_growth_1996_2021')

# Create output dataframe with town name and relevant columns
output_df = top_15[['name', 'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
                     'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
                     'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']].copy()

# Convert percentage columns from decimal to actual percentages (multiply by 100)
pct_cols = ['pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
            'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']
for col in pct_cols:
    output_df[col] = output_df[col] * 100

# Reset index for display
output_df = output_df.reset_index(drop=True)

density_cols = ['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']

# Create the GT table
gt = (
    GT(output_df, rowname_col='name')
    .tab_header(
        title="Ontario Population Growth Trends",
        subtitle="Top 15 Fastest-Growing Towns: Density Changes (1996-2021) & Population Change by Period"
    )
    .cols_label(
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        pop_change_1996_2001_pct="1996-2001",
        pop_change_2001_2006_pct="2001-2006",
        pop_change_2006_2011_pct="2006-2011",
        pop_change_2011_2016_pct="2011-2016",
        pop_change_2016_2021_pct="2016-2021"
    )
    .tab_spanner(
        label="Population Density (people/km²)",
        columns=density_cols
    )
    .tab_spanner(
        label="Population Change (%)",
        columns=pct_cols
    )
    .fmt_number(
        columns=density_cols,
        decimals=1
    )
    .fmt_number(
        columns=pct_cols,
        decimals=1,
        pattern="{x}%"
    )
    .cols_width(
        cases={
            'name': '180px',
            'density_1996': '90px',
            'density_2001': '90px',
            'density_2006': '90px',
            'density_2011': '90px',
            'density_2016': '90px',
            'density_2021': '90px',
            'pop_change_1996_2001_pct': '95px',
            'pop_change_2001_2006_pct': '95px',
            'pop_change_2006_2011_pct': '95px',
            'pop_change_2011_2016_pct': '95px',
            'pop_change_2016_2021_pct': '95px',
        }
    )
    .tab_options(
        heading_padding='6px',
        column_labels_padding='6px',
        column_labels_padding_horizontal='8px',
        data_row_padding='5px',
        data_row_padding_horizontal='8px',
        source_notes_padding='6px',
        table_body_hlines_style='solid',
        table_body_hlines_color=PALETTE['neutral']['hairline'],
        table_body_hlines_width='1px',
        column_labels_border_bottom_color=PALETTE['neutral']['column_label_rule'],
        column_labels_border_bottom_width='2px'
    )
    .tab_style(
        style=style.borders(
            sides='right',
            color=PALETTE['neutral']['vertical_divider'],
            weight='1px'
        ),
        locations=loc.body(columns='density_2021')
    )
    .tab_style(
        style=style.borders(
            sides='right',
            color=PALETTE['neutral']['vertical_divider'],
            weight='1px'
        ),
        locations=loc.column_labels(columns='density_2021')
    )
)

# Apply color fill to density columns (gradient showing increase over time)
gt = heatmap(gt, columns=density_cols, kind='sequential', hue='neutral')

# Apply color to population change columns (diverging for positive/negative)
gt = heatmap(gt, columns=pct_cols, kind='diverging', hue='default')

# Apply heading band
gt = band(gt)

# Apply striping and stub tint
gt = stripe(gt)
gt = stub_tint(gt)

# Apply frame
gt = frame(gt)

# Add caption and source note
gt = (
    gt
    .tab_source_note(
        source_note="Shows the top 15 Ontario towns with the highest population growth from 1996 to 2021, along with population density changes across census periods and percentage population growth for each interval."
    )
    .tab_source_note(
        source_note="Data source: Statistics Canada Census (1996-2021)"
    )
)

# Finalize with rendering
finalize(gt)
