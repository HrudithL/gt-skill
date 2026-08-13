import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Load and prepare data
df = pd.read_csv('towny.csv')

# Calculate overall growth from 1996 to 2021
df['pop_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'])

# Get top 15 fastest-growing towns, sorted by growth rate
top_15 = df.nlargest(15, 'pop_growth_pct').copy()
top_15 = top_15.sort_values('pop_growth_pct', ascending=False).reset_index(drop=True)

# Build display dataframe with specific columns
display_df = top_15[[
    'name',
    'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
    'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct'
]].copy()

# Rename columns for display
display_df.columns = [
    'Town',
    'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021',
    '1996–2001 %', '2001–2006 %', '2006–2011 %', '2011–2016 %', '2016–2021 %'
]

# Ensure numeric types
density_cols = ['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021']
pct_change_cols = ['1996–2001 %', '2001–2006 %', '2006–2011 %', '2011–2016 %', '2016–2021 %']

for col in density_cols + pct_change_cols:
    display_df[col] = pd.to_numeric(display_df[col])

# Create GT table
gt = GT(display_df, rowname_col='Town')

# Step 3: Color measures — density (magnitude, sequential Blues) and percent change (signed, diverging RdYlGn)
# Density domain
dens_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
dens_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

# Percent change domain (signed, symmetric)
pct_lo = float(np.nanmin(display_df[pct_change_cols].to_numpy()))
pct_hi = float(np.nanmax(display_df[pct_change_cols].to_numpy()))
pct_max = max(abs(pct_lo), abs(pct_hi))

# Apply formatting
gt = (
    gt.fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_change_cols, decimals=1, force_sign=True, scale_values=False)
    .sub_missing(columns=density_cols + pct_change_cols, missing_text="—")
)

# Apply density gradient (Blues for neutral magnitude)
gt = gt.data_color(
    columns=density_cols,
    palette='Blues',
    domain=[dens_lo, dens_hi],
    truncate=False,
    na_color="#808080"
)

# Apply percent change diverging fill (RdYlGn for growth, default orientation)
gt = gt.data_color(
    columns=pct_change_cols,
    palette='RdYlGn',
    reverse=False,
    domain=[-pct_max, pct_max],
    truncate=False,
    na_color="#808080"
)

# Step 4: Heading band
gt = band(gt)
gt = gt.tab_style(style=style.text(color="white"), locations=loc.column_labels())

# Step 5: Small color polish
# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Column-group vertical dividers (density vs pct change)
gt = (
    gt.tab_spanner(label="Population Density (people/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_change_cols)
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021"),
    )
)

# (c) Row striping
gt = gt.opt_row_striping()
gt = gt.tab_options(row_striping_background_color="#F6F6F6")

# (d) Stub tint
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Population Density and Growth Rates Across Census Years (1996–2021)"
    )
    .tab_source_note(
        source_note="Fastest-growing means highest population growth from 1996 to 2021. Density changes reflect shifting population relative to land area. Percent changes show population increase/decrease between consecutive Census periods."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

# (g) Compact layout
gt = gt.cols_width(cases={
    'Town': '160px',
    'Density 1996': '100px',
    'Density 2001': '100px',
    'Density 2006': '100px',
    'Density 2011': '100px',
    'Density 2016': '100px',
    'Density 2021': '100px',
    '1996–2001 %': '90px',
    '2001–2006 %': '90px',
    '2006–2011 %': '90px',
    '2011–2016 %': '90px',
    '2016–2021 %': '90px',
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Frame and render
gt = frame(gt)
gt.gtsave("table.png", expand=15)
