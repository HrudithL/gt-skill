import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

# Load data
df = pd.read_csv('towny.csv')

# Calculate overall growth from 1996 to 2021
df['total_growth_pct'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct')[['name',
                                               'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
                                               'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']].reset_index(drop=True)

# Rename columns for clarity
top_15 = top_15.rename(columns={
    'name': 'Town',
    'density_1996': '1996',
    'density_2001': '2001',
    'density_2006': '2006',
    'density_2011': '2011',
    'density_2016': '2016',
    'density_2021': '2021',
    'pop_change_1996_2001_pct': '1996–2001',
    'pop_change_2001_2006_pct': '2001–2006',
    'pop_change_2006_2011_pct': '2006–2011',
    'pop_change_2011_2016_pct': '2011–2016',
    'pop_change_2016_2021_pct': '2016–2021',
})

# Create GT table
tbl = GT(top_15)

# Add title and subtitle
tbl = tbl.tab_header(
    title="Ontario's Fastest-Growing Towns: Population Density & Growth Trends",
    subtitle=md("Density (persons per km²) and population change by census period, 1996–2021")
)

# Format density columns (per km²)
density_cols = ['1996', '2001', '2006', '2011', '2016', '2021']
tbl = tbl.fmt_number(columns=density_cols, decimals=1)

# Format percentage change columns (multiply by 100 and add %)
pct_cols = ['1996–2001', '2001–2006', '2006–2011', '2011–2016', '2016–2021']
tbl = tbl.fmt_percent(columns=pct_cols, decimals=1)

# Add spanners for logical grouping
tbl = tbl.tab_spanner(
    label="Population Density (per km²)",
    columns=density_cols
).tab_spanner(
    label="Population Change (%)",
    columns=pct_cols
)

# Substitute missing values
tbl = tbl.sub_missing(missing_text="—")

# Add source note
tbl = tbl.tab_source_note(source_note="Source: Statistics Canada census data, 1996–2021. Top 15 towns ranked by overall population growth 1996–2021.")

# Apply house style
tbl = apply_house_style(tbl)

# Add heatmap for percentage changes to highlight growth patterns
tbl = add_heatmap(tbl, top_15, pct_cols, kind="auto")

# Export
tbl.gtsave("table.png", zoom=2, expand=10)
