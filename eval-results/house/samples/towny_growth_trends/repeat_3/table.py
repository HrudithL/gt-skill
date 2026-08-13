import pandas as pd
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap
)

# Read data
df = pd.read_csv('towny.csv')

# Calculate overall growth 1996-2021 for ranking
df['overall_growth_pct'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns
top_15_df = df.nlargest(15, 'overall_growth_pct').copy()

# Build the display table with population, density, and period-change percentages
table_data = []
for _, row in top_15_df.iterrows():
    table_data.append({
        'Town': row['name'],
        'Pop 1996': row['population_1996'],
        'Density 1996': row['density_1996'],
        'Pop 2001': row['population_2001'],
        'Density 2001': row['density_2001'],
        'Pct Chg 96-01': row['pop_change_1996_2001_pct'],
        'Pop 2006': row['population_2006'],
        'Density 2006': row['density_2006'],
        'Pct Chg 01-06': row['pop_change_2001_2006_pct'],
        'Pop 2011': row['population_2011'],
        'Density 2011': row['density_2011'],
        'Pct Chg 06-11': row['pop_change_2006_2011_pct'],
        'Pop 2016': row['population_2016'],
        'Density 2016': row['density_2016'],
        'Pct Chg 11-16': row['pop_change_2011_2016_pct'],
        'Pop 2021': row['population_2021'],
        'Density 2021': row['density_2021'],
        'Pct Chg 16-21': row['pop_change_2016_2021_pct'],
        'Overall Growth': row['overall_growth_pct'],
    })

display_df = pd.DataFrame(table_data)

# Create GT table with stub (town names)
gt = GT(display_df, rowname_col='Town')

# Add title and subtitle
gt = gt.tab_header(
    title="Ontario Town Population Growth Trends",
    subtitle=md("Top 15 fastest-growing towns: population and density across census years, 1996–2021")
)

# Organize into column spanners for each census period
gt = gt.tab_spanner(label="1996", columns=['Pop 1996', 'Density 1996'])
gt = gt.tab_spanner(label="2001", columns=['Pop 2001', 'Density 2001', 'Pct Chg 96-01'])
gt = gt.tab_spanner(label="2006", columns=['Pop 2006', 'Density 2006', 'Pct Chg 01-06'])
gt = gt.tab_spanner(label="2011", columns=['Pop 2011', 'Density 2011', 'Pct Chg 06-11'])
gt = gt.tab_spanner(label="2016", columns=['Pop 2016', 'Density 2016', 'Pct Chg 11-16'])
gt = gt.tab_spanner(label="2021", columns=['Pop 2021', 'Density 2021', 'Pct Chg 16-21'])
gt = gt.tab_spanner(label="Overall", columns=['Overall Growth'])

# Format columns
gt = gt.fmt_integer(columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021'], use_seps=True)
gt = gt.fmt_number(
    columns=['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'],
    decimals=2
)
gt = gt.fmt_percent(
    columns=['Pct Chg 96-01', 'Pct Chg 01-06', 'Pct Chg 06-11', 'Pct Chg 11-16', 'Pct Chg 16-21', 'Overall Growth'],
    decimals=1
)

# Set column widths
gt = gt.cols_width(
    cases={
        'Pop 1996': '85px',
        'Density 1996': '90px',
        'Pop 2001': '85px',
        'Density 2001': '90px',
        'Pct Chg 96-01': '85px',
        'Pop 2006': '85px',
        'Density 2006': '90px',
        'Pct Chg 01-06': '85px',
        'Pop 2011': '85px',
        'Density 2011': '90px',
        'Pct Chg 06-11': '85px',
        'Pop 2016': '85px',
        'Density 2016': '90px',
        'Pct Chg 11-16': '85px',
        'Pop 2021': '85px',
        'Density 2021': '90px',
        'Pct Chg 16-21': '85px',
        'Overall Growth': '95px',
    }
)

# Set padding
gt = gt.tab_options(
    heading_padding='6px',
    column_labels_padding='6px',
    column_labels_padding_horizontal='8px',
    data_row_padding='5px',
    data_row_padding_horizontal='8px',
    source_notes_padding='6px',
)

# Apply heatmap coloring to percentage changes (diverging: green = good growth)
pct_cols = ['Pct Chg 96-01', 'Pct Chg 01-06', 'Pct Chg 06-11', 'Pct Chg 11-16', 'Pct Chg 16-21', 'Overall Growth']
gt = heatmap(gt, pct_cols, kind="diverging", hue="default")

# Apply sequential heatmap to population columns
pop_cols = ['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021']
gt = heatmap(gt, pop_cols, kind="sequential", hue="neutral")

# Styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by overall population growth (percent change 1996–2021). All municipality types included. "
                "Percentage changes are population growth rates between consecutive census periods."
)
gt = gt.tab_source_note(
    source_note="Source: Statistics Canada Census of Population, 1996–2021."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Render
finalize(gt)
