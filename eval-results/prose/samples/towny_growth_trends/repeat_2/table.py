import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021
df['overall_growth'] = (df['population_2021'] - df['population_1996']) / df['population_1996']

# Sort by overall growth and get top 15
top_15 = df.nlargest(15, 'overall_growth').copy()

# Select and organize columns for the table
# We'll show: name, density for each year, percent change between periods
table_df = top_15[[
    'name',
    'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct',
    'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct'
]].reset_index(drop=True)

# Rename columns for display
table_df.columns = [
    'Town',
    'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021',
    '1996-2001', '2001-2006', '2006-2011', '2011-2016', '2016-2021'
]

# Create the GT object with town names as stub
gt = GT(table_df, rowname_col='Town')

# Add column spanners for logical grouping
gt = (gt
    .tab_spanner(label='Population Density (persons/km²)', columns=[
        'Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021'
    ])
    .tab_spanner(label='Growth Rate Between Census Periods (%)', columns=[
        '1996-2001', '2001-2006', '2006-2011', '2011-2016', '2016-2021'
    ])
)

# Format density columns as numbers
density_cols = ['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021']
gt = gt.fmt_number(columns=density_cols, decimals=1, use_seps=True)

# Format percent change columns
pct_cols = ['1996-2001', '2001-2006', '2006-2011', '2011-2016', '2016-2021']
gt = gt.fmt_percent(columns=pct_cols, decimals=1, force_sign=True, scale_values=False)

# Compute domain for gradient fill on percent changes
pct_data = table_df[pct_cols].to_numpy()
pct_min = float(np.nanmin(pct_data))
pct_max = float(np.nanmax(pct_data))

# Apply data_color to growth rates - use Greens since growth is positive direction
gt = (gt
    .data_color(
        columns=pct_cols,
        palette="Greens",
        domain=[pct_min, pct_max],
        truncate=False,
        na_color="#808080"
    )
)

# Apply heading band styling
gt = (gt
    .tab_options(
        table_font_size="11px",
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px"
    )
)

# Style the header text to white for visibility on dark background
gt = gt.tab_style(
    style=style.text(color="white"),
    locations=loc.column_labels()
)

# Add stub tint
gt = (gt
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
)

# Add cell borders and row striping
gt = (gt
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px"
    )
    .opt_row_striping()
)

# Add column group dividers
gt = (gt
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021")
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021")
    )
)

# Add title, subtitle and footer notes
gt = (gt
    .tab_header(
        title="Ontario's 15 Fastest-Growing Towns: Population Density and Growth Rates",
        subtitle="Comparison of population density and intercensal growth across six Census periods (1996–2021)"
    )
    .tab_source_note(
        source_note="Fastest-growing towns ranked by total population growth from 1996 to 2021. Growth rates show percent change between consecutive Census periods."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

# Set frame and container options
gt = (gt
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px"
    )
)

# Render to PNG with margins
gt.gtsave("table.png", expand=15)
print("Table saved to table.png")
